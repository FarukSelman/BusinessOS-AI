from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.tools.analytics_tools import (
    GetAppointmentStatsTool,
    GetCustomerStatsTool,
    GetDashboardSummaryTool,
    GetReviewStatsTool,
    GetServicePopularityTool,
    GetStaffPerformanceTool,
    GetSurveyResultsTool,
)
from app.ai.agents.tools.base import BaseTool
from app.ai.openai.client import OpenAIClient


class AnalyticsAgent(BaseAgent):
    """
    Operasyonel Analiz Ajanı.

    Genel durum, randevu/müşteri/hizmet istatistikleri, personel
    performansı, anket ve yorum puanları. Tutarlar yalnızca
    OWNER/ADMIN rolüne gösterilir; ayrıntılı finans Finans Ajanı'ndadır.
    """

    def __init__(self, client: OpenAIClient, db: Session, business_id: UUID, user_id: UUID | None = None, role=None):
        super().__init__(client=client)
        common = dict(db=db, business_id=business_id, role=role)
        self._tools: list[BaseTool] = [
            GetDashboardSummaryTool(**common),
            GetAppointmentStatsTool(**common),
            GetCustomerStatsTool(**common),
            GetServicePopularityTool(**common),
            GetStaffPerformanceTool(**common),
            GetSurveyResultsTool(**common),
            GetReviewStatsTool(**common),
        ]

    @property
    def name(self) -> str:
        return "analytics"

    @property
    def description(self) -> str:
        return (
            "Operasyonel analiz: genel durum özeti, randevu/müşteri istatistikleri, popüler hizmetler, "
            "personel performansı, anket sonuçları ve yorum puanları."
        )

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin veri analiz asistanısın.

Kurallar:
1. "Durum nasıl / özet ver" sorularında önce get_dashboard_summary kullan.
2. Randevu, müşteri ve hizmet sorularında get_appointment_stats, get_customer_stats, get_service_popularity kullan; dönem belirtilmemişse bu ayı kullan ve bunu yanıtında söyle.
3. Personel karşılaştırmasında get_staff_performance, memnuniyet sorularında get_survey_results ve get_review_stats kullan.
4. Rakamları uydurma; sadece araç çıktısındaki verileri kullan.
5. Verileri tablo veya liste formatında sun, gerektiğinde karşılaştırma ve trend yorumu yap, somut öneride bulun.
6. Araç çıktısında tutarlar gizlenmişse bunları tahmin etme. Ciro, gider ve kâr gibi ayrıntılı finans soruları için kullanıcıya yetkisi varsa Finans asistanına sorabileceğini söyle.
7. Kullanıcıyla aynı dilde yanıt ver."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools
