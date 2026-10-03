"""
Analytics tools (Analytics agent, partly shared with Marketing).

All numbers come from ReportService / module services, the same source as
the Reports page, so the agent and the dashboard never disagree. Money
columns are only shown to OWNER / ADMIN (see common.can_view_finance).
"""
from datetime import date

from app.ai.agents.tools.base import ToolResult
from app.ai.agents.tools.common import (
    MAX_ROWS,
    PERIOD_LABELS,
    PERIOD_PARAMETER,
    BusinessTool,
    money,
    resolve_period,
)

FINANCE_HIDDEN_NOTE = "(Tutarlar yalnızca işletme sahibi ve yöneticilere gösterilir.)"

PERIOD_WITH_ALL = {
    **PERIOD_PARAMETER,
    "enum": PERIOD_PARAMETER["enum"] + ["all"],
    "description": PERIOD_PARAMETER["description"] + ", all=tüm zamanlar",
}


def _report_service(db):
    from app.modules.reports.repository import ReportRepository
    from app.modules.reports.service import ReportService

    return ReportService(ReportRepository(db))


def _period(kwargs, default="month"):
    if kwargs.get("period") == "all":
        return date(2000, 1, 1), date.today(), "Tüm zamanlar"
    return resolve_period(kwargs.get("period"), default=default)


class GetAppointmentStatsTool(BusinessTool):
    @property
    def name(self) -> str:
        return "get_appointment_stats"

    @property
    def description(self) -> str:
        return "Seçilen dönemdeki randevu istatistiklerini getirir: toplam, tamamlanan, iptal, gelmeyen, tamamlanma oranı ve hizmetlere göre dağılım."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"period": PERIOD_WITH_ALL}}

    def execute(self, **kwargs) -> ToolResult:
        start, end, label = _period(kwargs)
        r = _report_service(self.db).get_appointment_report(self.business_id, start, end)
        lines = [
            f"Randevu istatistikleri — {label}",
            f"Toplam: {r['total_appointments']}",
            f"Tamamlanan: {r['completed_count']}",
            f"İptal: {r['cancelled_count']}",
            f"Gelmeyen: {r.get('no_show_count', 0)}",
            f"Tamamlanma oranı: %{r['completion_rate']:.1f}",
        ]
        if r["by_service"]:
            lines.append("Hizmetlere göre:")
            for s in r["by_service"][:10]:
                extra = f" — {money(s['revenue'])}" if self.can_view_finance else ""
                lines.append(f"- {s['name']}: {s['booking_count']} randevu{extra}")
        return ToolResult(success=True, output="\n".join(lines))


class GetCustomerStatsTool(BusinessTool):
    @property
    def name(self) -> str:
        return "get_customer_stats"

    @property
    def description(self) -> str:
        return "Müşteri istatistiklerini getirir: toplam/aktif müşteri, dönemdeki yeni ve geri dönen müşteriler, en sık gelen müşteriler, aylık büyüme."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"period": PERIOD_PARAMETER}}

    def execute(self, **kwargs) -> ToolResult:
        from sqlalchemy import func

        from app.modules.customers.models import Customer

        start, end, label = resolve_period(kwargs.get("period"), default="month")
        report = _report_service(self.db).get_customer_report(self.business_id, start, end)
        by_status = dict(
            self.db.query(Customer.status, func.count(Customer.id))
            .filter(Customer.business_id == self.business_id, Customer.is_deleted.is_(False))
            .group_by(Customer.status)
            .all()
        )
        total = sum(by_status.values())
        lines = [
            "Müşteri istatistikleri",
            f"Toplam müşteri: {total}",
        ]
        for status, count in by_status.items():
            lines.append(f"- {getattr(status, 'value', status)}: {count}")
        lines += [
            f"{label}: {report['new_customers_count']} yeni müşteri, {report['returning_customers_count']} geri dönen müşteri",
        ]
        if report["top_customers"]:
            lines.append("En sık gelen müşteriler:")
            for c in report["top_customers"][:5]:
                spent = f", {money(c['total_spent'])}" if self.can_view_finance else ""
                lines.append(f"- {c['name']}: {c['visit_count']} ziyaret{spent}")
        if report["customer_growth"]:
            lines.append("Aylık yeni müşteri: " + ", ".join(f"{g['month'][:7]}: {g['count']}" for g in report["customer_growth"][-6:]))
        return ToolResult(success=True, output="\n".join(lines))


class GetServicePopularityTool(BusinessTool):
    @property
    def name(self) -> str:
        return "get_service_popularity"

    @property
    def description(self) -> str:
        return "Hizmetlerin popülerlik sıralamasını randevu sayısına göre getirir (varsayılan: son 90 gün)."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"period": PERIOD_WITH_ALL}}

    def execute(self, **kwargs) -> ToolResult:
        start, end, label = _period(kwargs, default="quarter")
        rows = _report_service(self.db).get_service_report(self.business_id, start, end)
        rows = sorted(rows, key=lambda r: r["booking_count"], reverse=True)
        if not rows:
            return ToolResult(success=True, output=f"{label} için hizmet verisi yok.")
        lines = [f"Hizmet popülerliği — {label}"]
        for i, r in enumerate(rows[:MAX_ROWS], 1):
            extra = f" — {money(r['revenue'])}" if self.can_view_finance else ""
            lines.append(f"{i}. {r['name']}: {r['booking_count']} randevu{extra}")
        return ToolResult(success=True, output="\n".join(lines))


class GetDashboardSummaryTool(BusinessTool):
    @property
    def name(self) -> str:
        return "get_dashboard_summary"

    @property
    def description(self) -> str:
        return "İşletmenin genel durum özetini getirir: müşteri sayısı, bugünkü ve bu ayki randevular, bekleyen randevular, aktif personel (yöneticiler için ayrıca bu ayın ciro, gider ve net kârı)."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs) -> ToolResult:
        s = _report_service(self.db).get_dashboard_stats(self.business_id)
        lines = [
            "Genel durum",
            f"Toplam müşteri: {s['total_customers']}",
            f"Bugünkü randevu: {s['total_appointments_today']}",
            f"Bu ayki randevu: {s['total_appointments_this_month']}",
            f"Bekleyen (onaylanmamış) randevu: {s['pending_appointments']}",
            f"Aktif personel: {s['active_staff_count']}",
        ]
        if self.can_view_finance:
            lines += [
                f"Bu ay ciro: {money(s['total_revenue_this_month'])}",
                f"Bu ay gider: {money(s['total_expenses_this_month'])}",
                f"Bu ay net kâr: {money(s['net_profit_this_month'])}",
            ]
        else:
            lines.append(FINANCE_HIDDEN_NOTE)
        return ToolResult(success=True, output="\n".join(lines))


class GetStaffPerformanceTool(BusinessTool):
    @property
    def name(self) -> str:
        return "get_staff_performance"

    @property
    def description(self) -> str:
        return "Personel performansını getirir: personel başına randevu sayısı ve tamamlanma oranı (yöneticiler için ciro)."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"period": PERIOD_PARAMETER}}

    def execute(self, **kwargs) -> ToolResult:
        start, end, label = resolve_period(kwargs.get("period"))
        rows = _report_service(self.db).get_staff_performance(self.business_id, start, end)
        if not rows:
            return ToolResult(success=True, output="Personel kaydı bulunamadı.")
        rows = sorted(rows, key=lambda r: r["appointment_count"], reverse=True)
        lines = [f"Personel performansı — {label}"]
        for r in rows[:MAX_ROWS]:
            title = f" ({r['title']})" if r.get("title") else ""
            extra = f", ciro {money(r['revenue'])}" if self.can_view_finance else ""
            lines.append(f"- {r['name']}{title}: {r['appointment_count']} randevu, tamamlanma %{r['completion_rate']:.0f}{extra}")
        return ToolResult(success=True, output="\n".join(lines))


class GetSurveyResultsTool(BusinessTool):
    @property
    def name(self) -> str:
        return "get_survey_results"

    @property
    def description(self) -> str:
        return "Anketlerin yanıt sayısını ve ortalama memnuniyet puanını getirir. Tek tek cevap metinlerini göstermez."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {"survey_title": {"type": "string", "description": "Belirli bir anket (opsiyonel, başlığın bir kısmı yeterli)"}},
        }

    def execute(self, **kwargs) -> ToolResult:
        from app.modules.surveys.repository import SurveyRepository, SurveyResponseRepository

        surveys = SurveyRepository(self.db).list_by_business(self.business_id, 1, 100)
        title = (kwargs.get("survey_title") or "").strip().lower()
        if title:
            surveys = [s for s in surveys if title in s.title.lower()]
        if not surveys:
            return ToolResult(success=True, output="Eşleşen anket bulunamadı.")
        responses = SurveyResponseRepository(self.db)
        lines = ["Anket sonuçları"]
        for s in surveys[:MAX_ROWS]:
            stats = responses.get_stats(s.id)
            status = getattr(s.status, "value", s.status)
            avg = f", ortalama puan {stats['average_rating']:.1f}/5" if stats["response_count"] else ""
            lines.append(f"- {s.title} [{status}]: {stats['response_count']} yanıt{avg}")
        return ToolResult(success=True, output="\n".join(lines))


class GetReviewStatsTool(BusinessTool):
    @property
    def name(self) -> str:
        return "get_review_stats"

    @property
    def description(self) -> str:
        return "Yayınlanmış müşteri yorumlarının ortalama puanını, sayısını ve puan dağılımını; ayrıca onay bekleyen ve yanıtlanmamış yorum sayısını getirir."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs) -> ToolResult:
        from sqlalchemy import func

        from app.modules.reviews.models import CustomerReview
        from app.modules.reviews.repository import CustomerReviewRepository
        from app.shared.enums.review import ReviewStatus

        s = CustomerReviewRepository(self.db).get_stats(self.business_id)
        base = self.db.query(func.count(CustomerReview.id)).filter(
            CustomerReview.business_id == self.business_id, CustomerReview.is_deleted.is_(False)
        )
        pending = base.filter(CustomerReview.status == ReviewStatus.PENDING).scalar()
        unreplied = base.filter(CustomerReview.status == ReviewStatus.PUBLISHED, CustomerReview.reply.is_(None)).scalar()
        dist = s.get("rating_distribution") or {}
        lines = [
            "Müşteri yorumları",
            f"Yayınlanmış yorum: {s.get('total_count', 0)}, ortalama puan: {float(s.get('average_rating') or 0):.2f}/5",
            "Dağılım: " + ", ".join(f"{k}★: {dist.get(k, dist.get(str(k), 0))}" for k in (5, 4, 3, 2, 1)),
            f"Onay bekleyen: {pending}, yanıtlanmamış (yayında): {unreplied}",
        ]
        return ToolResult(success=True, output="\n".join(lines))


__all__ = [
    "GetAppointmentStatsTool",
    "GetCustomerStatsTool",
    "GetServicePopularityTool",
    "GetDashboardSummaryTool",
    "GetStaffPerformanceTool",
    "GetSurveyResultsTool",
    "GetReviewStatsTool",
    "PERIOD_LABELS",
]
