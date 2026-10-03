from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.tools.base import BaseTool
from app.ai.agents.tools.rag_tools import (
    SearchKnowledgeBaseTool,
    GetBusinessInfoTool,
)
from app.ai.agents.tools.service_tools import (
    ListServicesTool,
)
from app.ai.agents.tools.analytics_tools import (
    GetCustomerStatsTool,
    GetServicePopularityTool,
)
from app.ai.agents.tools.campaign_tools import CreateCampaignDraftTool
from app.ai.embedding.service import EmbeddingService
from app.ai.openai.client import OpenAIClient


class MarketingAgent(BaseAgent):
    """
    Pazarlama ve Kampanya Öneri Ajanı.

    İşletmenin gerçek verilerine (hizmet popülerliği, müşteri
    istatistikleri, marka bilgisi) dayanarak kampanya, promosyon
    ve içerik önerileri üretir.
    """

    def __init__(
        self,
        client: OpenAIClient,
        db: Session,
        business_id: UUID,
        user_id: UUID,
        embedding_service: EmbeddingService,
    ):
        super().__init__(client=client)

        self._tools = [
            GetBusinessInfoTool(
                db=db,
                business_id=business_id,
            ),
            ListServicesTool(
                db=db,
                business_id=business_id,
            ),
            GetServicePopularityTool(
                db=db,
                business_id=business_id,
            ),
            GetCustomerStatsTool(
                db=db,
                business_id=business_id,
            ),
            SearchKnowledgeBaseTool(
                db=db,
                business_id=business_id,
                embedding_service=embedding_service,
            ),
            CreateCampaignDraftTool(
                db=db,
                business_id=business_id,
                requested_by=user_id,
            ),
        ]

    @property
    def name(self) -> str:
        return "marketing"

    @property
    def description(self) -> str:
        return (
            "Pazarlama ve kampanya önerisi yapar. Promosyon fikirleri, "
            "sosyal medya içerik önerileri, hedef kitle analizi ve "
            "kampanya stratejisi sunabilir."
        )

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin pazarlama asistanısın.

Görevin:
İşletmenin gerçek verilerine dayanarak somut, uygulanabilir pazarlama ve kampanya önerileri sunmak.

Kurallar:
1. Önce get_business_info ile işletmeyi tanı (sektör, marka tonu).
2. get_service_popularity ile hangi hizmetlerin popüler, hangilerinin
   az tercih edildiğini kontrol et — az tercih edilenler için promosyon öner.
3. get_customer_stats ile müşteri tabanının büyüklüğünü/trendini anla,
   önerilerini buna göre ölçekle (örn. yeni müşteri kazanımı mı, sadakat mı).
4. list_services ile fiyatları kontrol et, kampanya indirimlerini gerçekçi tut.
5. Gerekirse search_knowledge_base ile ek marka/ürün bilgisi ara.
6. Önerilerini somutlaştır: kampanya adı, hedef kitle, süre, olası mesaj/slogan.
7. İstenirse kısa sosyal medya gönderi metni de yazabilirsin.
8. Kullanıcı kampanyayı taslak olarak oluşturmak isterse create_campaign_draft aracını kullan. Araç mesaj göndermez ve yönetici onayı gerektirir.
9. Kullanıcıyla aynı dilde yanıt ver."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools
