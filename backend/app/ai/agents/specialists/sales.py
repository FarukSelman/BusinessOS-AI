from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.tools.base import BaseTool
from app.ai.agents.tools.catalog_tools import (
    GetCustomerPackagesTool,
    ListLowStockProductsTool,
    ListServicePackagesTool,
    SearchProductsTool,
)
from app.ai.agents.tools.rag_tools import SearchKnowledgeBaseTool
from app.ai.agents.tools.service_tools import GetServiceDetailsTool, ListServicesTool
from app.ai.embedding.service import EmbeddingService
from app.ai.openai.client import OpenAIClient


class SalesAgent(BaseAgent):
    """
    Satış Ajanı.

    Hizmet, ürün ve paket önerisi; fiyat ve stok bilgisi.
    """

    def __init__(
        self,
        client: OpenAIClient,
        db: Session,
        business_id: UUID,
        embedding_service: EmbeddingService,
        role=None,
    ):
        super().__init__(client=client)
        common = dict(db=db, business_id=business_id, role=role)
        self._tools: list[BaseTool] = [
            ListServicesTool(db=db, business_id=business_id),
            GetServiceDetailsTool(db=db, business_id=business_id),
            SearchKnowledgeBaseTool(db=db, business_id=business_id, embedding_service=embedding_service),
            SearchProductsTool(**common),
            ListLowStockProductsTool(**common),
            ListServicePackagesTool(**common),
            GetCustomerPackagesTool(**common),
        ]

    @property
    def name(self) -> str:
        return "sales"

    @property
    def description(self) -> str:
        return (
            "Satış asistanı: hizmet ve ürün önerisi, fiyat ve stok sorgulama, stoğu azalan ürünler, "
            "hizmet paketleri ve müşterinin aktif paketleri."
        )

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin satış asistanısın.

Kurallar:
1. Hizmet sorularında list_services ve gerekirse get_service_details kullan.
2. Ürün, fiyat ve stok sorularında search_products kullan; stokta olmayan ürünü önerme ya da stokta olmadığını belirt.
3. Stok takibi sorularında ("neler azaldı, ne sipariş etmeliyim") list_low_stock_products kullan. Stok değiştiremezsin.
4. Birden fazla seans gerektiren ihtiyaçlarda list_service_packages ile paket öner; paket fiyatını tek tek seans fiyatlarıyla karşılaştır.
5. Belirli bir müşterinin paketleri ve kalan seansları için get_customer_packages kullan; kalan seansı bitmek üzere olanlara yenileme öner.
6. Fiyatları her zaman belirt, karşılaştırma yaparak en uygun seçeneği öner.
7. Gerekirse search_knowledge_base ile ek ürün/hizmet bilgisi ara.
8. Samimi ve ikna edici bir dil kullan; kullanıcıyla aynı dilde yanıt ver."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools
