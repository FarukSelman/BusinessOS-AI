from uuid import UUID

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
)

from app.db.unit_of_work import UnitOfWork

from app.modules.document.models import Document
from app.modules.document.repository import DocumentRepository
from app.modules.document.schemas import (
    DocumentCreate,
    DocumentUpdate,
)

from app.shared.enums.document import DocumentStatus
from fastapi import UploadFile

from app.shared.storage.storage import StorageService
from app.modules.document_chunk.service import DocumentChunkService


class DocumentService:

    def __init__(
        self,
        repository: DocumentRepository,
        chunk_service: DocumentChunkService,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.chunk_service = chunk_service
        self.uow = uow

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    def upload_document(
        self,
        business_id: UUID,
        uploaded_by: UUID,
        file: UploadFile,
    ) -> Document:

        if file.filename is None:
            raise ConflictException(
                "Invalid filename."
            )

        if self.repository.exists_by_name(
            business_id,
            file.filename,
        ):
            raise ConflictException(
                "A document with the same filename already exists."
            )

        stored_filename, storage_path = StorageService.save(file)

        document = Document(
            business_id=business_id,
            uploaded_by=uploaded_by,

            file_name=stored_filename,
            original_name=file.filename,

            mime_type=file.content_type or "application/octet-stream",

            file_size=file.size or 0,

            storage_path=storage_path,

            status=DocumentStatus.UPLOADED,
        )

        with self.uow:

            self.repository.create(document)

            self.uow.flush()

            self.uow.refresh(document)

        # ---------------------------------------------
        # PROCESS DOCUMENT
        # ---------------------------------------------

        document.status = DocumentStatus.PROCESSING

        with self.uow:

            self.uow.flush()

        self.chunk_service.create_chunks(
            document_id=document.id,
            file_path=document.storage_path,
        )

        document.status = DocumentStatus.READY

        with self.uow:

            self.uow.flush()

            self.uow.refresh(document)

        return document

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    def get_document(
        self,
        document_id: UUID,
    ) -> Document:

        document = self.repository.get(
            document_id,
        )

        if document is None:
            raise NotFoundException(
                "Document not found."
            )

        return document

    # ---------------------------------------------------------
    # LIST
    # ---------------------------------------------------------

    def get_business_documents(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Document]:

        return self.repository.get_business_documents(
            business_id=business_id,
            page=page,
            size=size,
        )

    # ---------------------------------------------------------
    # UPDATE STATUS
    # ---------------------------------------------------------

    def update_document(
        self,
        document_id: UUID,
        data: DocumentUpdate,
    ) -> Document:

        document = self.get_document(
            document_id,
        )

        if data.status is not None:
            document.status = data.status

        with self.uow:

            self.uow.flush()

            self.uow.refresh(document)

        return document

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def delete_document(
        self,
        document_id: UUID,
    ) -> None:

        document = self.get_document(
            document_id,
        )

        with self.uow:

            self.repository.delete(
                document,
            )

            self.uow.flush()