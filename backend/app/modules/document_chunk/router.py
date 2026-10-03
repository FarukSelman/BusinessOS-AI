from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.document.repository import (
    DocumentRepository,
)

from app.modules.document_chunk.repository import (
    DocumentChunkRepository,
)

from app.modules.document_chunk.service import (
    DocumentChunkService,
)

from app.modules.document_chunk.schemas import (
    DocumentChunkResponse,
)

from app.modules.user.models import User

from app.shared.auth.permissions import Permission
from app.shared.security.permissions import require_permission

from app.ai.embedding.factory import (
    get_embedding_service,
)
from app.modules.document_chunk.search_schemas import (
    DocumentChunkSearchResponse,
)


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/businesses/{business_id}/documents/{document_id}/chunks",
    tags=["Document Chunks"],
)


# ==========================================================
# Dependency
# ==========================================================

def get_service(
    db: Session = Depends(get_db),
) -> DocumentChunkService:

    repository = DocumentChunkRepository(
        db,
    )

    uow = UnitOfWork(
        db,
    )

    embedding_service = get_embedding_service()

    return DocumentChunkService(
        repository=repository,
        embedding_service=embedding_service,
        uow=uow,
    )


def _verify_document_ownership(
    db: Session,
    business_id: UUID,
    document_id: UUID,
) -> None:
    """
    Ensures the document actually belongs to the given business,
    so one business cannot read another business's chunks by
    guessing a document_id.
    """

    document = DocumentRepository(db).get(document_id)

    if not document or document.business_id != business_id:
        raise NotFoundException("Document not found.")


# ==========================================================
# List Document Chunks
# ==========================================================

@router.get(
    "",
    response_model=list[DocumentChunkResponse],
    summary="List document chunks",
)
def list_document_chunks(
    business_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    service: DocumentChunkService = Depends(get_service),
    current_user: User = Depends(
        require_permission(Permission.DOCUMENT_READ),
    ),
):
    _verify_document_ownership(db, business_id, document_id)

    return service.get_document_chunks(
        document_id=document_id,
    )


# ==========================================================
# Search Chunks
# ==========================================================

@router.get(
    "/search",
    response_model=list[DocumentChunkSearchResponse],
    summary="Search document chunks",
)
def search_document_chunks(
    business_id: UUID,
    document_id: UUID,
    query: str,
    limit: int = 5,
    db: Session = Depends(get_db),
    service: DocumentChunkService = Depends(get_service),
    current_user: User = Depends(
        require_permission(Permission.DOCUMENT_READ),
    ),
):
    _verify_document_ownership(db, business_id, document_id)

    chunks = service.hybrid_search(
        document_id=document_id,
        query=query,
        limit=limit,
    )

    return [
        DocumentChunkSearchResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            score=score,
        )
        for chunk, score in chunks
    ]


# ==========================================================
# Get Single Chunk
# ==========================================================

@router.get(
    "/{chunk_id}",
    response_model=DocumentChunkResponse,
    summary="Get document chunk",
)
def get_document_chunk(
    business_id: UUID,
    document_id: UUID,
    chunk_id: UUID,
    db: Session = Depends(get_db),
    service: DocumentChunkService = Depends(get_service),
    current_user: User = Depends(
        require_permission(Permission.DOCUMENT_READ),
    ),
):
    _verify_document_ownership(db, business_id, document_id)

    return service.get_chunk(
        document_id=document_id,
        chunk_id=chunk_id,
    )