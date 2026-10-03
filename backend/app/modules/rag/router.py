from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.ai.rag.factory import get_rag_service
from app.ai.rag.schemas import (
    RAGRequest,
    RAGAnswerResponse,
)

from app.ai.rag.service import RAGService


from app.modules.user.models import User

from app.shared.security.permissions import (
    require_permission,
)

from app.shared.auth.permissions import (
    Permission,
)


router = APIRouter(
    prefix="/businesses/{business_id}/rag",
    tags=["RAG"],
)


@router.post(
    "/ask",
    response_model=RAGAnswerResponse,
    summary="Ask Business Knowledge Base",
)
def ask_question(
    business_id: UUID,

    request: RAGRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_permission(
            Permission.DOCUMENT_READ,
        )
    ),
):

    # -----------------------------------------
    # RAG Service
    # -----------------------------------------

    rag_service: RAGService = get_rag_service(
        db,
    )


    # -----------------------------------------
    # Ask RAG
    # -----------------------------------------

    result = rag_service.ask(
        # The URL path is the only source of truth for the business: it is
        # what the permission check above verified. Any business_id sent in
        # the body is ignored.
        business_id=business_id,

        user_id=current_user.id,

        question=request.question,

        top_k=request.top_k,
    )


    # -----------------------------------------
    # Response
    # -----------------------------------------

    return RAGAnswerResponse(
        answer=result.answer,

        sources=[
            chunk.chunk_id
            for chunk in result.retrieved_chunks
        ],
    )