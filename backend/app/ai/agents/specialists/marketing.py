from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.tools.analytics_tools import GetCustomerStatsTool, GetServicePopularityTool
from app.ai.agents.tools.base import BaseTool
from app.ai.agents.tools.campaign_tools import CreateCampaignDraftTool
from app.ai.agents.tools.customer_tools import GetLoyaltyInfoTool, ListCustomerSegmentsTool, ListReviewsTool
from app.ai.agents.tools.rag_tools import GetBusinessInfoTool, SearchKnowledgeBaseTool
from app.ai.agents.tools.service_tools import ListServicesTool
from app.ai.embedding.service import EmbeddingService
from app.ai.openai.client import OpenAIClient


class MarketingAgent(BaseAgent):
    """
    Pazarlama Ajanı.

    Kampanya fikri ve taslağı (onaylı), müşteri segmentleri, sadakat
    programı ve öne çıkarılabilecek müşteri yorumları.
    """

    def __init__(
        self,
        client: OpenAIClient,
        db: Session,
        business_id: UUID,
        user_id: UUID,
        embedding_service: EmbeddingService,
        role=None,
    ):
        super().__init__(client=client)
        common = dict(db=db, business_id=business_id, role=role)
        self._tools: list[BaseTool] = [
            GetBusinessInfoTool(db=db, business_id=business_id),
            ListServicesTool(db=db, business_id=business_id),
            GetServicePopularityTool(**common),
            GetCustomerStatsTool(**common),
            SearchKnowledgeBaseTool(db=db, business_id=business_id, embedding_service=embedding_service),
            CreateCampaignDraftTool(db=db, business_id=business_id, requested_by=user_id),
            ListCustomerSegmentsTool(**common),
            GetLoyaltyInfoTool(**common),
            ListReviewsTool(**common),
        ]

    @property
    def name(self) -> str:
        return "marketing"

    @property
    def description(self) -> str:
        return (
            "Pazarlama: kampanya fikri ve taslağı, sosyal medya metni, müşteri segmentleri (etiketler), "
            "sadakat puanı programı ve öne çıkarılacak olumlu yorumlar."
        )

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin pazarlama asistanısın.

Kurallar:
1. Önce get_business_info ile işletmeyi tanı (sektör, marka tonu).
2. get_service_popularity ile hangi hizmetlerin popüler, hangilerinin desteklenmesi gerektiğini belirle.
3. get_customer_stats ile müşteri tabanının büyüklüğünü ve trendini anla.
4. Hedef kitle seçerken list_customer_segments ile mevcut etiketleri ve segment büyüklüklerini kullan; kampanyanın hedef segmentini açıkça yaz.
5. Sadakat programıyla ilgili önerilerde get_loyalty_info kullan (puan değeri, bekleyen puanlar). Puan ekleyemez veya harcayamazsın.
6. Sosyal kanıt için list_reviews ile yüksek puanlı yayınlanmış yorumları (filter=published, min_rating=4) bul; yorumları değiştirmeden ve isim izni olduğunu varsaymadan, baş harfle kullan.
7. list_services ile fiyatları kontrol et, kampanya indirimlerini gerçekçi tut; gerekirse search_knowledge_base ile ek bilgi ara.
8. Önerilerini somutlaştır: kampanya adı, hedef segment, süre, teklif, mesaj/slogan. İstenirse kısa sosyal medya metni yaz.
9. Kullanıcı kampanyayı taslak olarak oluşturmak isterse create_campaign_draft kullan; araç mesaj göndermez ve yönetici onayı gerektirir.
10. Kullanıcıyla aynı dilde yanıt ver."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools
