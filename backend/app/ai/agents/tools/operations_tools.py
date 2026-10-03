"""
Operations tools: business hours, branches and staff (Appointment and
Customer Support agents). Read-only; the schedule-block draft tool lives in
draft_tools.py.
"""
from datetime import date

from app.ai.agents.tools.base import ToolResult
from app.ai.agents.tools.common import MAX_ROWS, BusinessTool

DAY_NAMES = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
# Explicit abbreviations: slicing would turn both Pazartesi and Pazar into "Paz".
DAY_SHORT = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]


def find_branch(db, business_id, name: str | None):
    """(branch, None) / (None, None) when no name given / (None, error)."""
    from app.modules.branches.repository import BranchRepository

    name = (name or "").strip()
    if not name:
        return None, None
    branches = BranchRepository(db).list_by_business(business_id, 1, 100)
    matches = [b for b in branches if name.lower() in b.name.lower()]
    if len(matches) == 1:
        return matches[0], None
    if not matches:
        return None, f"'{name}' adında şube bulunamadı. Şubeler: " + ", ".join(b.name for b in branches)
    return None, f"Birden fazla şube eşleşti: {', '.join(b.name for b in matches)}. Lütfen netleştirin."


class GetBusinessHoursTool(BusinessTool):
    @property
    def name(self) -> str:
        return "get_business_hours"

    @property
    def description(self) -> str:
        return (
            "İşletmenin (veya bir şubenin) haftalık çalışma saatlerini getirir. Tarih verilirse o gün açık mı, "
            "hangi saatler arası açık ve o güne ait kapatmalar (tatil, mola) da gösterilir."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "branch_name": {"type": "string", "description": "Şube adı (opsiyonel)"},
                "date": {"type": "string", "description": "Belirli bir gün (YYYY-MM-DD, opsiyonel)"},
            },
        }

    def execute(self, **kwargs) -> ToolResult:
        from app.db.unit_of_work import UnitOfWork
        from app.modules.branches.repository import BranchRepository
        from app.modules.business_hours.repository import BusinessHoursRepository
        from app.modules.business_hours.service import BusinessHoursService
        from app.modules.schedule_blocks.repository import ScheduleBlockRepository
        from app.shared.enums.schedule_block import BlockType

        branch, error = find_branch(self.db, self.business_id, kwargs.get("branch_name"))
        if error:
            return ToolResult(success=False, output=error)
        branch_id = branch.id if branch else None
        service = BusinessHoursService(BusinessHoursRepository(self.db), UnitOfWork(self.db), BranchRepository(self.db))

        scope = f"{branch.name} şubesi" if branch else "İşletme"
        rows = service.get_hours(self.business_id, branch_id) if branch_id else []
        source = "şubeye özel"
        if not rows:
            rows = service.get_hours(self.business_id, None)
            source = "işletme geneli"
        lines = []
        if not rows:
            lines.append(f"{scope}: çalışma saati tanımlanmamış; varsayılan olarak her gün 09:00–18:00 randevu verilir.")
        else:
            lines.append(f"{scope} çalışma saatleri ({source}):")
            by_day = {r.day_of_week: r for r in rows}
            for d, day in enumerate(DAY_NAMES):
                r = by_day.get(d)
                if r is None or r.is_closed:
                    lines.append(f"- {day}: Kapalı")
                else:
                    lines.append(f"- {day}: {r.open_time:%H:%M}–{r.close_time:%H:%M}")

        if kwargs.get("date"):
            try:
                target = date.fromisoformat(kwargs["date"])
            except ValueError:
                return ToolResult(success=False, output="Geçersiz tarih. YYYY-MM-DD kullanın.")
            window = service.get_open_window(self.business_id, target, branch_id)
            blocks = ScheduleBlockRepository(self.db).list_active_blocks_for_date(self.business_id, target, branch_id)
            day_label = f"{target} ({DAY_NAMES[target.weekday()]})"
            if window is None or any(b.block_type == BlockType.FULL_DAY for b in blocks):
                lines.append(f"{day_label}: kapalı.")
            else:
                lines.append(f"{day_label}: {window[0]:%H:%M}–{window[1]:%H:%M} arası açık.")
            for b in blocks:
                if b.block_type != BlockType.FULL_DAY and b.start_time and b.end_time:
                    lines.append(f"  Kapatma: {b.start_time:%H:%M}–{b.end_time:%H:%M} {('— ' + b.title) if b.title else ''}".rstrip())
                elif b.block_type == BlockType.FULL_DAY and (b.title or b.reason):
                    lines.append(f"  Sebep: {b.title or b.reason}")
        return ToolResult(success=True, output="\n".join(lines))


class ListBranchesTool(BusinessTool):
    @property
    def name(self) -> str:
        return "list_branches"

    @property
    def description(self) -> str:
        return "İşletmenin şubelerini adres ve telefon bilgileriyle listeler."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.branches.repository import BranchRepository

        branches = [b for b in BranchRepository(self.db).list_by_business(self.business_id, 1, 100) if b.is_active]
        if not branches:
            return ToolResult(success=True, output="Kayıtlı şube yok; işletme tek lokasyonda hizmet veriyor.")
        lines = ["Şubeler:"]
        for b in branches[:MAX_ROWS]:
            parts = [p for p in (b.address, b.phone) if p]
            lines.append(f"- {b.name}{' (merkez)' if b.is_main else ''}: {' — '.join(parts) if parts else 'adres girilmemiş'}")
        return ToolResult(success=True, output="\n".join(lines))


class ListStaffTool(BusinessTool):
    @property
    def name(self) -> str:
        return "list_staff"

    @property
    def description(self) -> str:
        return "Aktif personeli; verdikleri hizmetler, şubeleri ve çalıştıkları gün/saatlerle listeler. Hizmet veya şubeye göre filtrelenebilir."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Bu hizmeti veren personel (opsiyonel)"},
                "branch_name": {"type": "string", "description": "Şube (opsiyonel)"},
            },
        }

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.branches.models import Branch
        from app.modules.staff.repository import StaffProfileRepository, StaffScheduleRepository, StaffServiceRepository

        branch, error = find_branch(self.db, self.business_id, kwargs.get("branch_name"))
        if error:
            return ToolResult(success=False, output=error)
        staff = StaffProfileRepository(self.db).list_active(self.business_id, branch.id if branch else None)
        services_repo, schedule_repo = StaffServiceRepository(self.db), StaffScheduleRepository(self.db)
        wanted = (kwargs.get("service_name") or "").strip().lower()
        branch_names = dict(self.db.query(Branch.id, Branch.name).filter(Branch.business_id == self.business_id).all())

        lines = []
        for s in staff:
            services = services_repo.list_services_for_staff(s.id)
            if wanted and not any(wanted in svc.name.lower() for svc in services):
                continue
            schedule = [d for d in schedule_repo.get_schedule_for_staff(s.id) if d.is_working]
            hours = ", ".join(f"{DAY_SHORT[d.day_of_week]} {d.start_time:%H:%M}-{d.end_time:%H:%M}" for d in schedule) or "çalışma saati girilmemiş"
            svc_text = ", ".join(svc.name for svc in services) or "hizmet atanmamış"
            where = branch_names.get(s.branch_id, "tüm şubeler") if s.branch_id else "tüm şubeler"
            title = f" ({s.title})" if s.title else ""
            lines.append(f"- {s.full_name}{title} — {where}; hizmetler: {svc_text}; çalışma: {hours}")
            if len(lines) >= MAX_ROWS:
                break
        if not lines:
            return ToolResult(success=True, output="Kriterlere uyan aktif personel bulunamadı.")
        return ToolResult(success=True, output="Personel:\n" + "\n".join(lines))
