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
from app.ai.embedding.service import EmbeddingService
from app.ai.openai.client import OpenAIClient


class CustomerSupportAgent(BaseAgent):
    """
    Müşteri Destek Ajanı.

    Müşterilerin sorularını işletmenin bilgi tabanı
    ve hizmet bilgileri kullanarak yanıtlar.
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
            SearchKnowledgeBaseTool(
                db=db,
                business_id=business_id,
                embedding_service=embedding_service,
            ),
            GetBusinessInfoTool(
                db=db,
                business_id=business_id,
            ),
            ListServicesTool(
                db=db,
                business_id=business_id,
            ),
        ]

    @property
    def name(self) -> str:
        return "customer_support"

    @property
    def description(self) -> str:
        return (
            "Müşteri sorularını yanıtlar. Fiyatlar, hizmetler, "
            "çalışma saatleri, SSS gibi genel bilgi sorularını "
            "işletmenin bilgi tabanından cevaplayabilir."
        )

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin müşteri destek asistanısın.

Görevin:
Müşterilerin sorularını işletmenin bilgi tabanı ve hizmet bilgilerini kullanarak yanıtlamak.

Kurallar:
1. Önce search_knowledge_base aracıyla bilgi tabanında ara.
2. Gerekirse list_services ile hizmet bilgilerini getir.
3. Gerekirse get_business_info ile işletme bilgilerini getir.
4. Sadece araçlardan gelen bilgilere dayanarak cevap ver.
5. Bilgi bulunamazsa kibarca bilmediğini söyle.
6. Cevapları kısa, anlaşılır ve yardımcı şekilde oluştur.
7. Kullanıcıyla aynı dilde yanıt ver.
8. Teknik terimlerden (RAG, embedding vb.) bahsetme."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools
