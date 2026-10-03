from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.tools.base import BaseTool
from app.ai.agents.tools.rag_tools import (
    SearchKnowledgeBaseTool,
)
from app.ai.agents.tools.service_tools import (
    ListServicesTool,
    GetServiceDetailsTool,
)
from app.ai.embedding.service import EmbeddingService
from app.ai.openai.client import OpenAIClient


class SalesAgent(BaseAgent):
    """
    Satış ve Ürün Öneri Ajanı.

    Müşterilere uygun ürün/hizmet önerir,
    fiyat bilgisi verir ve satışı destekler.
    """

    def __init__(
        self,
        client: OpenAIClient,
        db: Session,
        business_id: UUID,
        embedding_service: EmbeddingService,
    ):
        super().__init__(client=client)

        self._tools = [
            ListServicesTool(
                db=db,
                business_id=business_id,
            ),
            GetServiceDetailsTool(
                db=db,
                business_id=business_id,
            ),
            SearchKnowledgeBaseTool(
                db=db,
                business_id=business_id,
                embedding_service=embedding_service,
            ),
        ]

    @property
    def name(self) -> str:
        return "sales"

    @property
    def description(self) -> str:
        return (
            "Satış ve ürün önerisi yapar. Hizmet/ürün fiyatları, "
            "detayları, karşılaştırma ve müşteriye özel "
            "öneriler sunabilir."
        )

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin satış asistanısın.

Görevin:
Müşterilere en uygun ürün ve hizmetleri önermek, fiyat bilgisi vermek ve satışı desteklemek.

Kurallar:
1. Önce list_services ile mevcut hizmetleri kontrol et.
2. Detay için get_service_details aracını kullan.
3. Gerekirse search_knowledge_base ile ek bilgi ara.
4. Müşterinin ihtiyacına göre proaktif önerilerde bulun.
5. Fiyatları her zaman belirt.
6. Karşılaştırma yaparak en uygun seçeneği öner.
7. Samimi ve ikna edici bir dil kullan.
8. Kullanıcıyla aynı dilde yanıt ver."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools
