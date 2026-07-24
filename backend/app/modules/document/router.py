from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.document.repository import DocumentRepository
from app.modules.document.schemas import (
    DocumentResponse,
)
from app.modules.document.service import DocumentService

from app.modules.user.models import User

from app.shared.auth.permissions import Permission
from app.shared.security.permissions import require_permission
from app.modules.document_chunk.repository import DocumentChunkRepository
from app.modules.document_chunk.service import DocumentChunkService

from app.ai.embedding.service import EmbeddingService
from app.ai.embedding.providers.mock_provider import MockEmbeddingProvider


router = APIRouter(
    prefix="/businesses/{business_id}/documents",
    tags=["Documents"],
)


# ---------------------------------------------------------
# Dependency
# ---------------------------------------------------------

def get_service(
    db: Session = Depends(get_db),
) -> DocumentService:

    document_repository = DocumentRepository(db)

    chunk_repository = DocumentChunkRepository(db)

    uow = UnitOfWork(db)

    embedding_service = EmbeddingService(
        provider=MockEmbeddingProvider(),
    )

    chunk_service = DocumentChunkService(
        repository=chunk_repository,
        embedding_service=embedding_service,
        uow=uow,
    )

    return DocumentService(
        repository=document_repository,
        chunk_service=chunk_service,
        uow=uow,
    )

# ---------------------------------------------------------
# Upload Document
# ---------------------------------------------------------

@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(

    business_id: UUID,

    file: UploadFile = File(...),

    service: DocumentService = Depends(get_service),

    current_user: User = Depends(
        require_permission(
            Permission.DOCUMENT_UPLOAD,
        )
    ),
):

    return service.upload_document(
        business_id=business_id,
        uploaded_by=current_user.id,
        file=file,
    )


# ---------------------------------------------------------
# List Documents
# ---------------------------------------------------------

@router.get(
    "",
    response_model=list[DocumentResponse],
    summary="List documents",
)
def list_documents(
    business_id: UUID,

    service: DocumentService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.DOCUMENT_READ,
        )
    ),
):

    return service.list_documents(
        business_id=business_id,
    )


# ---------------------------------------------------------
# Get Document
# ---------------------------------------------------------

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document",
)
def get_document(
    business_id: UUID,

    document_id: UUID,

    service: DocumentService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.DOCUMENT_READ,
        )
    ),
):

    return service.get_document(
        business_id=business_id,
        document_id=document_id,
    )


# ---------------------------------------------------------
# Delete Document
# ---------------------------------------------------------

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
)
def delete_document(
    business_id: UUID,

    document_id: UUID,

    service: DocumentService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.DOCUMENT_DELETE,
        )
    ),
):

    service.delete_document(
        business_id=business_id,
        document_id=document_id,
    )