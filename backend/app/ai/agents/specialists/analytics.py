from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.tools.base import BaseTool
from app.ai.agents.tools.analytics_tools import (
    GetAppointmentStatsTool,
    GetCustomerStatsTool,
    GetServicePopularityTool,
)
from app.ai.agents.tools.invoice_tools import CreateInvoiceDraftTool
from app.ai.openai.client import OpenAIClient


class AnalyticsAgent(BaseAgent):
    """
    Finansal Raporlama ve Analiz Ajanı.

    İşletme verilerini analiz eder,
    istatistikler ve raporlar sunar.
    """

    def __init__(
        self,
        client: OpenAIClient,
        db: Session,
        business_id: UUID,
        user_id: UUID,
    ):
        super().__init__(client=client)

        self._tools = [
            GetAppointmentStatsTool(
                db=db,
                business_id=business_id,
            ),
            GetCustomerStatsTool(
                db=db,
                business_id=business_id,
            ),
            GetServicePopularityTool(
                db=db,
                business_id=business_id,
            ),
            CreateInvoiceDraftTool(
                db=db,
                business_id=business_id,
                requested_by=user_id,
            ),
        ]

    @property
    def name(self) -> str:
        return "analytics"

    @property
    def description(self) -> str:
        return (
            "İşletme analitiği ve raporlama yapar. "
            "Randevu istatistikleri, müşteri sayıları, "
            "hizmet popülerliği gibi verileri raporlar."
        )

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin veri analiz asistanısın.

Görevin:
İşletme verilerini analiz etmek ve anlaşılır raporlar sunmak.

Kurallar:
1. İstatistik soruları için uygun araçları kullan.
2. Verileri tablo veya liste formatında sun. Kullanıcı fatura oluşturmak isterse create_invoice_draft aracını kullan; bu araç yalnızca onay bekleyen taslak oluşturur.
3. Gerektiğinde karşılaştırma ve trend analizi yap.
4. Sayısal verileri anlaşılır bir şekilde yorumla.
5. Önerilerde bulun (örn: "En popüler hizmetiniz X, buna odaklanabilirsiniz").
6. Kullanıcıyla aynı dilde yanıt ver."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools
