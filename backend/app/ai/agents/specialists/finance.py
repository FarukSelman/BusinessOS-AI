from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.schemas import AgentContext, AgentResponse
from app.ai.agents.tools.base import BaseTool
from app.ai.agents.tools.common import can_view_finance
from app.ai.agents.tools.finance_tools import (
    FINANCE_DENIED,
    GetCashRegisterStatusTool,
    GetExpenseSummaryTool,
    GetInvoiceStatsTool,
    GetRevenueReportTool,
    ListOverdueInstallmentsTool,
)
from app.ai.agents.tools.draft_tools import CreateExpenseDraftTool
from app.ai.agents.tools.invoice_tools import CreateInvoiceDraftTool
from app.ai.openai.client import OpenAIClient


class FinanceAgent(BaseAgent):
    """
    Finans Ajanı: gelir, gider, kasa, taksit ve fatura.
    Yalnızca OWNER ve ADMIN rolündeki üyeler kullanabilir.
    """

    def __init__(self, client: OpenAIClient, db: Session, business_id: UUID, user_id: UUID, role=None):
        super().__init__(client=client)
        common = dict(db=db, business_id=business_id, role=role)
        self._tools: list[BaseTool] = [
            GetRevenueReportTool(**common),
            GetExpenseSummaryTool(**common),
            GetCashRegisterStatusTool(**common),
            ListOverdueInstallmentsTool(**common),
            GetInvoiceStatsTool(**common),
            CreateInvoiceDraftTool(db=db, business_id=business_id, requested_by=user_id),
            CreateExpenseDraftTool(**common, user_id=user_id),
        ]

    @property
    def name(self) -> str:
        return "finance"

    @property
    def description(self) -> str:
        return "Gelir, gider, net kâr, kasa durumu, geciken taksitler ve faturalarla ilgili soruları yanıtlar."

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin finans asistanısın.

Görevin işletme sahibine ve yöneticilerine gelir, gider, kasa, taksit ve fatura konularında yardımcı olmak.

Kurallar:
1. Rakam vermeden önce mutlaka ilgili aracı çağır; tahmin etme.
2. Dönem belirtilmemişse "bu ay" (month) kullan ve bunu yanıtında belirt.
3. Tutarları TL olarak, binlik ayraçla yaz.
4. Kasa açma/kapama, ödeme alma veya taksit tahsil etme gibi işlemleri yapamazsın; kullanıcıyı ilgili ekrana yönlendir.
5. Fatura oluşturmak istenirse create_invoice_draft, gider kaydetmek istenirse ("bugün 500 TL kira ödedim") create_expense_draft kullan; ikisi de yalnızca yönetici onayı bekleyen taslak oluşturur. Tutar veya tarih belirsizse önce sor.
6. Yorum yaparken somut ol: en büyük gider kalemi, geçen döneme göre değişim, geciken tahsilatlar gibi.
7. Kullanıcıyla aynı dilde yanıt ver."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools

    def execute(self, *, question: str, context: AgentContext, history=None) -> AgentResponse:
        # Defence in depth: the orchestrator already refuses non-finance roles.
        if not can_view_finance(context.role):
            return AgentResponse(answer=FINANCE_DENIED, agent_name=self.name, metadata={"access_denied": True})
        return super().execute(question=question, context=context, history=history)
