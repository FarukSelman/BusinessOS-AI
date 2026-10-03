"""
Approval-required write tools.

None of these change business data directly: each one validates its input,
stores an AgentAction (status PENDING) and returns it to the chat, where an
admin approves or rejects it. AgentActionService re-validates everything at
approval time before executing.
"""
from datetime import date, datetime, time

from app.ai.agents.tools.base import ToolResult
from app.ai.agents.tools.common import BusinessTool, money
from app.ai.agents.tools.finance_tools import FINANCE_DENIED


def _save_action(tool: BusinessTool, action_type: str, payload: dict):
    from app.modules.agent_actions.models import AgentAction

    action = AgentAction(
        business_id=tool.business_id,
        requested_by=tool.user_id,
        action_type=action_type,
        status="PENDING",
        payload=payload,
    )
    tool.db.add(action)
    tool.db.commit()
    tool.db.refresh(action)
    return {"action_id": str(action.id), "action_type": action_type, "payload": payload}


def _parse_date(value, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field} geçersiz; YYYY-MM-DD formatında olmalı.") from exc


def _parse_time(value, field: str) -> time:
    try:
        return time.fromisoformat(str(value)[:5])
    except ValueError as exc:
        raise ValueError(f"{field} geçersiz; SS:DD formatında olmalı.") from exc


# ---------------------------------------------------------------- expenses (Finance)

PAYMENT_METHODS = ["CASH", "CREDIT_CARD", "BANK_TRANSFER", "OTHER"]
PAYMENT_LABELS = {"CASH": "Nakit", "CREDIT_CARD": "Kredi kartı", "BANK_TRANSFER": "Havale/EFT", "OTHER": "Diğer"}


class CreateExpenseDraftTool(BusinessTool):
    @property
    def name(self) -> str:
        return "create_expense_draft"

    @property
    def description(self) -> str:
        return (
            "Kullanıcının anlattığı gideri (ör. 'bugün 500 TL kira ödedim') yönetici onayı bekleyen gider kaydı taslağına çevirir. "
            "Onaylanana kadar kayıt oluşmaz."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Kısa başlık, ör. 'Ekim kirası'"},
                "amount": {"type": "number", "exclusiveMinimum": 0, "description": "Tutar (TL)"},
                "transaction_date": {"type": "string", "description": "Tarih (YYYY-MM-DD, varsayılan bugün)"},
                "category_name": {"type": "string", "description": "Mevcut gider kategorisi adı (opsiyonel)"},
                "payment_method": {"type": "string", "enum": PAYMENT_METHODS},
                "description": {"type": "string", "description": "Açıklama (opsiyonel)"},
            },
            "required": ["title", "amount"],
        }

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.expense_categories.models import ExpenseCategory

        if not self.can_view_finance:
            return ToolResult(success=False, output=FINANCE_DENIED)
        try:
            title = str(kwargs.get("title") or "").strip()[:200]
            amount = round(float(kwargs.get("amount") or 0), 2)
            if not title or amount <= 0:
                return ToolResult(success=False, output="Gider için başlık ve sıfırdan büyük bir tutar gerekli.")
            tx_date = _parse_date(kwargs["transaction_date"], "Tarih") if kwargs.get("transaction_date") else date.today()
            if tx_date > date.today():
                return ToolResult(success=False, output="Gelecek tarihli gider kaydı oluşturulamaz.")
        except (ValueError, TypeError) as exc:
            return ToolResult(success=False, output=str(exc))

        categories = self.db.query(ExpenseCategory).filter(
            ExpenseCategory.business_id == self.business_id, ExpenseCategory.is_deleted.is_(False)
        ).all()
        category = None
        wanted = (kwargs.get("category_name") or "").strip().lower()
        if wanted:
            matches = [c for c in categories if wanted in c.name.lower()]
            if len(matches) != 1:
                names = ", ".join(c.name for c in categories) or "tanımlı kategori yok"
                return ToolResult(success=False, output=f"'{kwargs['category_name']}' kategorisi netleştirilemedi. Mevcut kategoriler: {names}")
            category = matches[0]

        method = kwargs.get("payment_method") if kwargs.get("payment_method") in PAYMENT_METHODS else None
        payload = {
            "direction": "EXPENSE",
            "title": title,
            "amount": amount,
            "transaction_date": tx_date.isoformat(),
            "category_id": str(category.id) if category else None,
            "category_name": category.name if category else "Kategorisiz",
            "payment_method": method,
            "payment_method_label": PAYMENT_LABELS.get(method),
            "description": (kwargs.get("description") or None),
        }
        data = _save_action(self, "CREATE_EXPENSE", payload)
        return ToolResult(
            success=True,
            output=f"Gider taslağı oluşturuldu; yönetici onayı bekleniyor. {title}: {money(amount)} ({tx_date}, {payload['category_name']}).",
            data=data,
        )


# ---------------------------------------------------------------- review replies (Customer Support)

class DraftReviewReplyTool(BusinessTool):
    @property
    def name(self) -> str:
        return "draft_review_reply"

    @property
    def description(self) -> str:
        return (
            "Yayınlanmış bir müşteri yorumuna işletme adına yanıt taslağı hazırlar. Yanıt, yönetici onaylayınca yayınlanır. "
            "Yorumu list_reviews çıktısındaki referans koduyla (#abc12345) belirt."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "review_ref": {"type": "string", "description": "list_reviews çıktısındaki referans kodu, ör. #1a2b3c4d"},
                "reply": {"type": "string", "description": "Kibar, kısa ve kişisel yanıt metni (en fazla 1000 karakter)"},
            },
            "required": ["review_ref", "reply"],
        }

    def execute(self, **kwargs) -> ToolResult:
        from sqlalchemy import String, cast

        from app.modules.reviews.models import CustomerReview
        from app.shared.enums.review import ReviewStatus

        ref = str(kwargs.get("review_ref") or "").strip().lstrip("#").lower()
        reply = str(kwargs.get("reply") or "").strip()
        if len(ref) < 6:
            return ToolResult(success=False, output="Geçerli bir yorum referans kodu gerekli (list_reviews çıktısındaki #kod).")
        if not reply:
            return ToolResult(success=False, output="Yanıt metni boş olamaz.")
        if len(reply) > 1000:
            return ToolResult(success=False, output="Yanıt en fazla 1000 karakter olabilir.")

        matches = self.db.query(CustomerReview).filter(
            CustomerReview.business_id == self.business_id,
            CustomerReview.is_deleted.is_(False),
            cast(CustomerReview.id, String).like(f"{ref}%"),
        ).limit(2).all()
        if len(matches) != 1:
            return ToolResult(success=False, output="Bu referans koduyla tek bir yorum bulunamadı.")
        review = matches[0]
        if review.status != ReviewStatus.PUBLISHED:
            return ToolResult(success=False, output="Yalnızca yayınlanmış yorumlara yanıt verilebilir; önce yorumun onaylanması gerekir.")
        if review.reply:
            return ToolResult(success=False, output="Bu yorum zaten yanıtlanmış.")

        comment = (review.comment or "").strip()
        payload = {
            "review_id": str(review.id),
            "reviewer_name": review.reviewer_name,
            "rating": review.rating,
            "review_comment": comment[:500] + ("…" if len(comment) > 500 else ""),
            "reply": reply,
        }
        data = _save_action(self, "REPLY_TO_REVIEW", payload)
        return ToolResult(success=True, output="Yanıt taslağı oluşturuldu; yönetici onaylayınca yorumun altında yayınlanacak.", data=data)


# ---------------------------------------------------------------- schedule blocks (Appointment)

BLOCK_TYPES = ["FULL_DAY", "TIME_RANGE", "RECURRING"]
BLOCK_LABELS = {"FULL_DAY": "Tüm gün kapalı", "TIME_RANGE": "Saat aralığı kapalı", "RECURRING": "Her hafta tekrarlayan"}
DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
DAY_LABELS = dict(zip(DAYS, ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]))


class CreateScheduleBlockDraftTool(BusinessTool):
    @property
    def name(self) -> str:
        return "create_schedule_block_draft"

    @property
    def description(self) -> str:
        return (
            "Takvimi kapatma taslağı oluşturur (izin, tatil, mola, bakım). FULL_DAY: tüm gün (date, ops. end_date); "
            "TIME_RANGE: bir günde saat aralığı (date, start_time, end_time); RECURRING: her hafta (recurrence_day, start_time, end_time). "
            "Onaylanınca o saatlerde randevu verilmez."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "block_type": {"type": "string", "enum": BLOCK_TYPES},
                "date": {"type": "string", "description": "Gün (YYYY-MM-DD) — FULL_DAY ve TIME_RANGE için"},
                "end_date": {"type": "string", "description": "Çok günlü FULL_DAY için son gün (opsiyonel)"},
                "start_time": {"type": "string", "description": "SS:DD"},
                "end_time": {"type": "string", "description": "SS:DD"},
                "recurrence_day": {"type": "string", "enum": DAYS},
                "branch_name": {"type": "string", "description": "Sadece bu şube için (opsiyonel; boşsa tüm işletme)"},
                "title": {"type": "string", "description": "Kısa başlık, ör. 'Öğle arası'"},
                "reason": {"type": "string"},
            },
            "required": ["block_type"],
        }

    def execute(self, **kwargs) -> ToolResult:
        from app.ai.agents.tools.operations_tools import find_branch
        from app.modules.appointments.models import Appointment
        from app.shared.enums.appointment import AppointmentStatus

        block_type = kwargs.get("block_type")
        if block_type not in BLOCK_TYPES:
            return ToolResult(success=False, output="block_type FULL_DAY, TIME_RANGE veya RECURRING olmalı.")
        branch, error = find_branch(self.db, self.business_id, kwargs.get("branch_name"))
        if error:
            return ToolResult(success=False, output=error)

        try:
            start_date = end_date = start_time = end_time = None
            recurrence_day = None
            if block_type in ("FULL_DAY", "TIME_RANGE"):
                if not kwargs.get("date"):
                    return ToolResult(success=False, output="Bu kapatma türü için tarih (date) gerekli.")
                start_date = _parse_date(kwargs["date"], "Tarih")
                if start_date < date.today():
                    return ToolResult(success=False, output="Geçmiş bir tarih için kapatma oluşturulamaz.")
            if block_type == "FULL_DAY" and kwargs.get("end_date"):
                end_date = _parse_date(kwargs["end_date"], "Bitiş tarihi")
                if end_date < start_date:
                    return ToolResult(success=False, output="Bitiş tarihi başlangıçtan önce olamaz.")
            if block_type in ("TIME_RANGE", "RECURRING"):
                if not kwargs.get("start_time") or not kwargs.get("end_time"):
                    return ToolResult(success=False, output="Başlangıç ve bitiş saati gerekli.")
                start_time = _parse_time(kwargs["start_time"], "Başlangıç saati")
                end_time = _parse_time(kwargs["end_time"], "Bitiş saati")
                if start_time >= end_time:
                    return ToolResult(success=False, output="Başlangıç saati bitiş saatinden önce olmalı.")
            if block_type == "RECURRING":
                recurrence_day = kwargs.get("recurrence_day")
                if recurrence_day not in DAYS:
                    return ToolResult(success=False, output="Tekrarlayan kapatma için gün (recurrence_day) gerekli.")
        except ValueError as exc:
            return ToolResult(success=False, output=str(exc))

        # Warn about appointments that already sit in the closed period (single-date blocks only).
        conflicts = 0
        if start_date:
            q = self.db.query(Appointment).filter(
                Appointment.business_id == self.business_id,
                Appointment.is_deleted.is_(False),
                Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]),
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= (end_date or start_date),
            )
            if branch:
                q = q.filter(Appointment.branch_id == branch.id)
            if start_time and end_time:
                q = q.filter(Appointment.start_time < end_time, Appointment.end_time > start_time)
            conflicts = q.count()

        payload = {
            "block_type": block_type,
            "block_type_label": BLOCK_LABELS[block_type],
            "branch_id": str(branch.id) if branch else None,
            "branch_name": branch.name if branch else "Tüm işletme",
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "start_time": start_time.strftime("%H:%M") if start_time else None,
            "end_time": end_time.strftime("%H:%M") if end_time else None,
            "recurrence_day": recurrence_day,
            "recurrence_day_label": DAY_LABELS.get(recurrence_day),
            "title": (kwargs.get("title") or None),
            "reason": (kwargs.get("reason") or None),
            "conflicting_appointments": conflicts,
        }
        data = _save_action(self, "CREATE_SCHEDULE_BLOCK", payload)
        warn = f" Dikkat: bu aralıkta {conflicts} mevcut randevu var; kapatma onaylansa da bu randevular iptal edilmez." if conflicts else ""
        return ToolResult(success=True, output="Kapatma taslağı oluşturuldu; yönetici onayı bekleniyor." + warn, data=data)
