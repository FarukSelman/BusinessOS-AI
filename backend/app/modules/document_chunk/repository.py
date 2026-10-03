from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.document_chunk.models import DocumentChunk



class DocumentChunkRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    def create(
        self,
        chunk: DocumentChunk,
    ) -> DocumentChunk:

        self.db.add(chunk)

        return chunk

    # ---------------------------------------------------------
    # BULK CREATE
    # ---------------------------------------------------------

    def bulk_create(
        self,
        chunks: list[DocumentChunk],
    ) -> None:

        self.db.add_all(chunks)

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    def get(
        self,
        chunk_id: UUID,
    ) -> DocumentChunk | None:

        return self.db.get(
            DocumentChunk,
            chunk_id,
        )

    # ---------------------------------------------------------
    # LIST BY DOCUMENT
    # ---------------------------------------------------------

    def get_document_chunks(
        self,
        document_id: UUID,
    ) -> list[DocumentChunk]:

        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.is_deleted.is_(False),
            )
            .order_by(
                DocumentChunk.chunk_index.asc(),
            )
        )

        return list(
            self.db.scalars(stmt).all()
        )

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------

    def search(
        self,
        document_id: UUID,
        query: str,
        limit: int = 10,
    ) -> list[DocumentChunk]:

        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.is_deleted.is_(False),
                DocumentChunk.content.ilike(f"%{query}%"),
            )
            .order_by(
                DocumentChunk.chunk_index.asc(),
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    # ---------------------------------------------------------
    # HARD DELETE ALL CHUNKS OF DOCUMENT
    # ---------------------------------------------------------

    def delete_by_document(
        self,
        document_id: UUID,
    ) -> None:

        stmt = (
            delete(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
            )
        )

        self.db.execute(stmt)

    # ---------------------------------------------------------
    # SOFT DELETE SINGLE CHUNK
    # ---------------------------------------------------------

    def delete(
        self,
        chunk: DocumentChunk,
    ) -> None:

        chunk.is_deleted = True

    # ---------------------------------------------------------
    # COUNT BY DOCUMENT
    # ---------------------------------------------------------

    def count_by_document(
        self,
        document_id: UUID,
    ) -> int:

        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.is_deleted.is_(False),
            )
        )

        return len(
            self.db.scalars(stmt).all()
        )


    # ---------------------------------------------------------
    # COUNT EMBEDDED
    # ---------------------------------------------------------

    def count_embedded(
        self,
        document_id: UUID,
    ) -> int:

        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.embedding.is_not(None),
                DocumentChunk.is_deleted.is_(False),
            )
        )

        return len(
            self.db.scalars(stmt).all()
        )


    # ---------------------------------------------------------
    # VECTOR SEARCH
    # ---------------------------------------------------------

    def semantic_search(
        self,
        *,
        document_id: UUID,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[DocumentChunk]:

        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.embedding.is_not(None),
                DocumentChunk.is_deleted.is_(False),
            )
            .order_by(
                DocumentChunk.embedding.cosine_distance(
                    query_embedding
                )
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    # ---------------------------------------------------------
    # HYBRID SEARCH
    # ---------------------------------------------------------

    def hybrid_search(
        self,
        *,
        document_id: UUID,
        query: str,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[DocumentChunk]:

        keyword_results = self.search(
            document_id=document_id,
            query=query,
            limit=limit,
        )

        semantic_results = self.semantic_search(
            document_id=document_id,
            query_embedding=query_embedding,
            limit=limit,
        )

        merged: dict[UUID, DocumentChunk] = {}

        for chunk in keyword_results:
            merged[chunk.id] = chunk

        for chunk in semantic_results:
            merged[chunk.id] = chunk

        return list(merged.values())[:limit]