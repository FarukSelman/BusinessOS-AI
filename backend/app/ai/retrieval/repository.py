from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.retrieval.schemas import (
    RetrievedChunk,
    RetrievalResult,
)

from app.modules.document.models import Document
from app.modules.document_chunk.models import DocumentChunk

from app.shared.enums.document import DocumentStatus
from app.shared.enums.document_chunk import EmbeddingStatus


class RetrievalRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def search(
        self,
        *,
        business_id: UUID,
        embedding: list[float],
        top_k: int = 5,
    ) -> RetrievalResult:
        """
        Semantic vector search using pgvector.
        """

        similarity = DocumentChunk.embedding.cosine_distance(
            embedding,
        )

        stmt = (
            select(
                DocumentChunk,
                similarity.label("similarity"),
            )
            .join(
                Document,
                Document.id == DocumentChunk.document_id,
            )
            .where(
                Document.business_id == business_id,
                Document.status == DocumentStatus.READY,
                DocumentChunk.embedding.is_not(None),
                DocumentChunk.embedding_status
                == EmbeddingStatus.COMPLETED,
                Document.is_deleted.is_(False),
                DocumentChunk.is_deleted.is_(False),
            )
            .order_by(similarity.asc())
            .limit(top_k)
        )

        rows = self.db.execute(stmt).all()

        chunks = [
            RetrievedChunk(
                chunk_id=row.DocumentChunk.id,
                document_id=row.DocumentChunk.document_id,
                chunk_index=row.DocumentChunk.chunk_index,
                content=row.DocumentChunk.content,
                similarity=float(row.similarity),
                embedding_model=row.DocumentChunk.embedding_model,
            )
            for row in rows
        ]

        return RetrievalResult(
            chunks=chunks,
        )