from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.tools.base import BaseTool, ToolResult
from app.ai.embedding.service import EmbeddingService
from app.ai.retrieval.repository import RetrievalRepository
from app.ai.retrieval.schemas import RetrievalResult


class SearchKnowledgeBaseTool(BaseTool):
    """
    Searches the business knowledge base using RAG.
    """

    def __init__(
        self,
        db: Session,
        business_id: UUID,
        embedding_service: EmbeddingService,
    ):
        self.db = db
        self.business_id = business_id
        self.embedding_service = embedding_service
        self.repository = RetrievalRepository(db=db)

    @property
    def name(self) -> str:
        return "search_knowledge_base"

    @property
    def description(self) -> str:
        return (
            "İşletmenin bilgi tabanında arama yapar. "
            "Yüklenen dokümanlardan ilgili bilgileri getirir. "
            "Fiyatlar, hizmetler, SSS gibi bilgiler için kullan."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Aranacak sorgu metni",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Döndürülecek sonuç sayısı",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs) -> ToolResult:

        query = kwargs.get("query", "")
        top_k = kwargs.get("top_k", 5)

        try:

            embedding = self.embedding_service.embed(query)

            result: RetrievalResult = self.repository.search(
                business_id=self.business_id,
                embedding=embedding,
                top_k=top_k,
            )

            if result.is_empty:
                return ToolResult(
                    success=True,
                    output="Bilgi tabanında ilgili sonuç bulunamadı.",
                )

            context = result.context

            return ToolResult(
                success=True,
                output=context,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Arama hatası: {str(e)}",
            )


class GetBusinessInfoTool(BaseTool):
    """
    Retrieves business information.
    """

    def __init__(
        self,
        db: Session,
        business_id: UUID,
    ):
        self.db = db
        self.business_id = business_id

    @property
    def name(self) -> str:
        return "get_business_info"

    @property
    def description(self) -> str:
        return (
            "İşletmenin temel bilgilerini getirir: "
            "ad, sektör, iletişim bilgileri vb."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
        }

    def execute(self, **kwargs) -> ToolResult:

        from app.modules.business.models import Business

        try:

            business = (
                self.db.query(Business)
                .filter(
                    Business.id == self.business_id,
                    Business.is_deleted.is_(False),
                )
                .first()
            )

            if not business:
                return ToolResult(
                    success=False,
                    output="İşletme bulunamadı.",
                )

            info = (
                f"İşletme Adı: {business.name}\n"
                f"Sektör: {business.industry}\n"
                f"E-posta: {business.email}\n"
                f"Telefon: {business.phone}\n"
                f"Website: {business.website or 'Belirtilmemiş'}\n"
            )

            return ToolResult(
                success=True,
                output=info,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Hata: {str(e)}",
            )
