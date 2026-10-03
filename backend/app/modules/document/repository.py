from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.document.models import Document


class DocumentRepository:

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
        document: Document,
    ) -> Document:

        self.db.add(document)

        return document

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    def get(
        self,
        document_id: UUID,
    ) -> Document | None:

        return self.db.get(
            Document,
            document_id,
        )

    def get_by_business(
        self,
        business_id: UUID,
        document_id: UUID,
    ) -> Document | None:

        stmt = (
            select(Document)
            .where(
                Document.id == document_id,
                Document.business_id == business_id,
                Document.is_deleted.is_(False),
            )
        )

        return self.db.scalar(stmt)

    # ---------------------------------------------------------
    # LIST BUSINESS DOCUMENTS
    # ---------------------------------------------------------

    def get_business_documents(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 20, 
    ) -> list[Document]:

        stmt = (
            select(Document)
            .where(
                Document.business_id == business_id,
                Document.is_deleted.is_(False),
            )
            .offset(
                (page - 1) * size,
            )
            .limit(size)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    # ---------------------------------------------------------
    # EXISTS
    # ---------------------------------------------------------

    def exists_by_name(
        self,
        business_id: UUID,
        file_name: str,
    ) -> bool:

        stmt = (
            select(Document)
            .where(
                Document.business_id == business_id,
                Document.file_name == file_name,
                Document.is_deleted.is_(False),
            )
        )

        return self.db.scalar(stmt) is not None

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    def update(
        self,
        document: Document,
    ) -> Document:

        return document

    # ---------------------------------------------------------
    # SOFT DELETE
    # ---------------------------------------------------------

    def delete(
        self,
        document: Document,
    ) -> None:

        document.is_deleted = True