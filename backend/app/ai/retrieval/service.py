from uuid import UUID

from app.ai.embedding.service import EmbeddingService
from app.ai.retrieval.repository import RetrievalRepository
from app.ai.retrieval.schemas import RetrievalResult


class RetrievalService:
    """
    High-level semantic retrieval service.

    Converts a user query into an embedding,
    performs vector search and returns the
    most relevant document chunks.
    """

    def __init__(
        self,
        repository: RetrievalRepository,
        embedding_service: EmbeddingService,
    ):
        self.repository = repository
        self.embedding_service = embedding_service

    def retrieve(
        self,
        *,
        business_id: UUID,
        query: str,
        top_k: int = 3,
    ) -> RetrievalResult:
        """
        Retrieve the most relevant chunks
        for a user query.
        """

        query_embedding = self.embedding_service.embed(
            query,
        )

        result = self.repository.search(
            business_id=business_id,
            embedding=query_embedding,
            top_k=top_k,
        )


        if not result.chunks:
            return result


        return result