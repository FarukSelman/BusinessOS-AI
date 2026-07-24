from uuid import UUID

from sqlalchemy import select
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
    # DELETE
    # ---------------------------------------------------------

    def delete(
        self,
        chunk: DocumentChunk,
    ) -> None:

        chunk.is_deleted = True