from uuid import UUID

from fastapi import UploadFile, BackgroundTasks

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
)

from app.db.unit_of_work import UnitOfWork

from app.modules.document.models import Document
from app.modules.document.repository import DocumentRepository
from app.modules.document.schemas import (
    DocumentUpdate,
    DocumentStatusResponse,
)

from app.modules.document.tasks import process_document

from app.modules.document_chunk.service import DocumentChunkService

from app.shared.enums.document import DocumentStatus
from app.shared.storage.storage import StorageService


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
    # CREATE DOCUMENT
    # ---------------------------------------------------------

    def upload_document(
        self,
        business_id: UUID,
        uploaded_by: UUID,
        file: UploadFile,
        background_tasks: BackgroundTasks,
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


        stored_filename, storage_path = StorageService.save(
            file
        )


        document = Document(
            business_id=business_id,
            uploaded_by=uploaded_by,

            file_name=stored_filename,
            original_name=file.filename,

            mime_type=file.content_type
            or "application/octet-stream",

            file_size=file.size
            or 0,

            storage_path=storage_path,

            status=DocumentStatus.UPLOADED,
        )


        with self.uow:

            self.repository.create(
                document
            )

            self.uow.flush()

            self.uow.refresh(
                document
            )


        # ---------------------------------------------
        # ASYNC PROCESSING
        # ---------------------------------------------

        background_tasks.add_task(
            process_document,
            document.id,
        )


        return document



    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    def get_document(
        self,
        business_id: UUID,
        document_id: UUID,
    ) -> Document:


        document = self.repository.get_by_business(
            business_id=business_id,
            document_id=document_id,
        )


        if document is None:

            raise NotFoundException(
                "Document not found."
            )


        return document



    # ---------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------

    def get_document_status(
        self,
        business_id: UUID,
        document_id: UUID,
    ) -> DocumentStatusResponse:


        document = self.get_document(
            business_id,
            document_id,
        )


        return DocumentStatusResponse(
            id=document.id,
            status=document.status,
        )



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



    def list_documents(
        self,
        business_id: UUID,
    ) -> list[Document]:

        return self.get_business_documents(
            business_id
        )



    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    def update_document(
        self,
        business_id: UUID,
        document_id: UUID,
        data: DocumentUpdate,
    ) -> Document:


        document = self.get_document(
            business_id,
            document_id,
        )


        if data.status is not None:

            document.status = data.status


        with self.uow:

            self.uow.flush()

            self.uow.refresh(
                document
            )


        return document



    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def delete_document(
        self,
        business_id: UUID,
        document_id: UUID,
    ) -> None:


        document = self.get_document(
            business_id,
            document_id,
        )


        with self.uow:

            self.repository.delete(
                document
            )

            self.uow.flush()