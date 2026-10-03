"""
Finance tools (Finance agent). Only reachable for OWNER / ADMIN: the
orchestrator refuses the finance agent for other roles, and every tool
re-checks the role as a second line of defence.
"""
from datetime import date

from app.ai.agents.tools.base import ToolResult
from app.ai.agents.tools.common import (
    MAX_ROWS,
    PERIOD_PARAMETER,
    BusinessTool,
    money,
    resolve_period,
)

FINANCE_DENIED = "Bu finansal bilgi yalnızca işletme sahibi ve yöneticileri tarafından görüntülenebilir."


class _FinanceTool(BusinessTool):
    def execute(self, **kwargs) -> ToolResult:
        if not self.can_view_finance:
            return ToolResult(success=False, output=FINANCE_DENIED)
        return self.run(**kwargs)

    def run(self, **kwargs) -> ToolResult:  # pragma: no cover - abstract
        raise NotImplementedError


class GetRevenueReportTool(_FinanceTool):
    @property
    def name(self) -> str:
        return "get_revenue_report"

    @property
    def description(self) -> str:
        return "Seçilen dönem için gelir, gider ve net kâr raporunu (günlük/haftalık/aylık kırılımla) getirir."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "period": PERIOD_PARAMETER,
                "group_by": {"type": "string", "enum": ["daily", "weekly", "monthly"], "description": "Kırılım (varsayılan: daily)"},
            },
        }

    def run(self, **kwargs) -> ToolResult:
        from app.modules.reports.repository import ReportRepository
        from app.modules.reports.service import ReportService

        start, end, label = resolve_period(kwargs.get("period"))
        group_by = kwargs.get("group_by") if kwargs.get("group_by") in ("daily", "weekly", "monthly") else "daily"
        rows = ReportService(ReportRepository(self.db)).get_revenue_report(self.business_id, start, end, group_by)
        income = sum(r["income"] for r in rows)
        expense = sum(r["expense"] for r in rows)
        lines = [
            f"Gelir raporu — {label} ({start} – {end})",
            f"Toplam gelir: {money(income)}",
            f"Toplam gider: {money(expense)}",
            f"Net: {money(income - expense)}",
        ]
        if rows:
            lines.append("Dönem | Gelir | Gider | Net | Fatura")
            for r in rows[-31:]:
                lines.append(f"{r['period']} | {money(r['income'])} | {money(r['expense'])} | {money(r['net'])} | {r['invoice_count']}")
        else:
            lines.append("Bu dönemde gelir/gider kaydı yok.")
        return ToolResult(success=True, output="\n".join(lines))


class GetExpenseSummaryTool(_FinanceTool):
    @property
    def name(self) -> str:
        return "get_expense_summary"

    @property
    def description(self) -> str:
        return "Seçilen dönemde toplam gelir/gider kayıtlarını ve giderlerin kategori bazında dağılımını getirir."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"period": PERIOD_PARAMETER}}

    def run(self, **kwargs) -> ToolResult:
        from app.db.unit_of_work import UnitOfWork
        from app.modules.expenses.repository import ExpenseRepository
        from app.modules.expenses.service import ExpenseService

        start, end, label = resolve_period(kwargs.get("period"))
        repo = ExpenseRepository(self.db)
        summary = ExpenseService(repo, UnitOfWork(self.db)).get_summary(self.business_id, start, end)
        breakdown = repo.get_expense_breakdown_by_category(self.business_id, start, end)
        lines = [
            f"Gelir/gider kayıtları — {label} ({start} – {end})",
            f"Toplam gelir kaydı: {money(summary.total_income)}",
            f"Toplam gider: {money(summary.total_expense)}",
            f"Net: {money(summary.net_profit)}",
        ]
        if breakdown:
            lines.append("Kategori | Tutar | Kayıt sayısı")
            for b in breakdown[:MAX_ROWS]:
                lines.append(f"{b['category']} | {money(b['total'])} | {b['count']}")
        return ToolResult(success=True, output="\n".join(lines))


class GetCashRegisterStatusTool(_FinanceTool):
    @property
    def name(self) -> str:
        return "get_cash_register_status"

    @property
    def description(self) -> str:
        return "Bugünkü (veya açık) kasanın durumunu ve açılış, satış, gider, beklenen kapanış özetini getirir. Kasa açıp kapatmaz."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    def run(self, **kwargs) -> ToolResult:
        from app.db.unit_of_work import UnitOfWork
        from app.modules.cash_register.repository import CashRegisterRepository, CashTransactionRepository
        from app.modules.cash_register.service import CashRegisterService

        reg_repo = CashRegisterRepository(self.db)
        register = reg_repo.get_by_date(self.business_id, date.today()) or reg_repo.get_open_register(self.business_id)
        if register is None:
            return ToolResult(success=True, output="Bugün için açılmış bir kasa yok.")
        service = CashRegisterService(reg_repo, CashTransactionRepository(self.db), UnitOfWork(self.db))
        s = service.get_register_summary(register.id, business_id=self.business_id)
        status = getattr(register.status, "value", register.status)
        lines = [
            f"Kasa ({register.register_date}) — durum: {'Açık' if status == 'OPEN' else 'Kapalı'}",
            f"Açılış: {money(s.opening_balance)}",
            f"Satış: {money(s.total_sales)}",
            f"Para girişi: {money(s.total_deposits)}",
            f"Gider: {money(s.total_expenses)}",
            f"Para çıkışı: {money(s.total_withdrawals)}",
            f"Beklenen kapanış: {money(s.expected_closing)}",
        ]
        return ToolResult(success=True, output="\n".join(lines))


class ListOverdueInstallmentsTool(_FinanceTool):
    @property
    def name(self) -> str:
        return "list_overdue_installments"

    @property
    def description(self) -> str:
        return "Vadesi geçmiş, ödenmemiş paket taksitlerini müşteri, tutar ve gecikme günüyle listeler."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    def run(self, **kwargs) -> ToolResult:
        from app.modules.customers.models import Customer
        from app.modules.packages.repository import InstallmentRepository

        items = InstallmentRepository(self.db).list_overdue(self.business_id)
        if not items:
            return ToolResult(success=True, output="Vadesi geçmiş taksit yok.")
        names = dict(self.db.query(Customer.id, Customer.name).filter(
            Customer.id.in_({i.customer_id for i in items}), Customer.business_id == self.business_id,
        ).all())
        today = date.today()
        total = sum(float(i.amount) for i in items)
        lines = [f"Vadesi geçmiş {len(items)} taksit, toplam {money(total)}", "Müşteri | Taksit no | Tutar | Vade | Gecikme"]
        for i in items[:MAX_ROWS]:
            lines.append(f"{names.get(i.customer_id, '-')} | {i.installment_number} | {money(i.amount)} | {i.due_date} | {(today - i.due_date).days} gün")
        if len(items) > MAX_ROWS:
            lines.append(f"... ve {len(items) - MAX_ROWS} taksit daha")
        return ToolResult(success=True, output="\n".join(lines))


class GetInvoiceStatsTool(_FinanceTool):
    @property
    def name(self) -> str:
        return "get_invoice_stats"

    @property
    def description(self) -> str:
        return "Fatura özetini getirir: tahsil edilen toplam, ödenmiş, taslak ve gecikmiş fatura sayıları."

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    def run(self, **kwargs) -> ToolResult:
        from app.modules.invoice.repository import InvoiceRepository

        s = InvoiceRepository(self.db).get_revenue_stats(self.business_id)
        return ToolResult(success=True, output="\n".join([
            "Fatura özeti (tüm zamanlar)",
            f"Tahsil edilen toplam: {money(s['total_revenue'])}",
            f"Ödenmiş fatura: {s['paid_count']}",
            f"Taslak fatura: {s['pending_count']}",
            f"Gecikmiş fatura: {s['overdue_count']}",
        ]))
