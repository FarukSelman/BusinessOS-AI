from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.base import BaseAgent
from app.ai.agents.tools.base import BaseTool
from app.ai.agents.tools.customer_tools import ListReviewsTool
from app.ai.agents.tools.draft_tools import DraftReviewReplyTool
from app.ai.agents.tools.operations_tools import GetBusinessHoursTool, ListBranchesTool
from app.ai.agents.tools.rag_tools import GetBusinessInfoTool, SearchKnowledgeBaseTool
from app.ai.agents.tools.service_tools import ListServicesTool
from app.ai.embedding.service import EmbeddingService
from app.ai.openai.client import OpenAIClient


class CustomerSupportAgent(BaseAgent):
    """
    Müşteri Destek Ajanı.

    Bilgi tabanı, işletme/şube bilgileri, çalışma saatleri, hizmetler
    ve müşteri yorumları.
    """

    def __init__(
        self,
        client: OpenAIClient,
        db: Session,
        business_id: UUID,
        embedding_service: EmbeddingService,
        user_id: UUID | None = None,
        role=None,
    ):
        super().__init__(client=client)
        common = dict(db=db, business_id=business_id, role=role)
        self._tools: list[BaseTool] = [
            SearchKnowledgeBaseTool(db=db, business_id=business_id, embedding_service=embedding_service),
            GetBusinessInfoTool(db=db, business_id=business_id),
            ListServicesTool(db=db, business_id=business_id),
            GetBusinessHoursTool(**common),
            ListBranchesTool(**common),
            ListReviewsTool(**common),
            DraftReviewReplyTool(**common, user_id=user_id),
        ]

    @property
    def name(self) -> str:
        return "customer_support"

    @property
    def description(self) -> str:
        return (
            "Müşteri sorularını yanıtlar: çalışma saatleri, şube adresleri, hizmetler, SSS ve bilgi tabanı; "
            "müşteri yorumlarını listeler ve yorumlara yanıt taslağı hazırlar."
        )

    @property
    def system_prompt(self) -> str:
        return """Sen {business_name} işletmesinin müşteri destek asistanısın.

Kurallar:
1. Çalışma saatleri ve "şu gün açık mısınız" sorularında get_business_hours kullan; bilgi tabanındaki eski saatlere güvenme.
2. Adres ve telefon sorularında list_branches ve get_business_info kullan.
3. Hizmet ve fiyat sorularında list_services kullan.
4. Diğer sorularda (politikalar, SSS, ürün bilgisi) search_knowledge_base ile bilgi tabanında ara.
5. Müşteri yorumları için list_reviews kullan. Yanıt yazılması istenirse yorumu okuyup kısa, kibar, kişisel bir yanıt hazırla ve draft_review_reply ile taslak oluştur; yanıt yönetici onayından sonra yayınlanır. Olumsuz yorumlarda özür dile, çözüm öner, tartışmaya girme.
6. Sadece araçlardan gelen bilgilere dayanarak cevap ver; bilgi bulunamazsa kibarca bilmediğini söyle.
7. Cevapları kısa, anlaşılır ve yardımcı şekilde oluştur; teknik terimlerden (RAG, embedding vb.) bahsetme.
8. Kullanıcıyla aynı dilde yanıt ver."""

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools
