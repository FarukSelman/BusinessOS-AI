from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.shared.security.dependencies import (
    get_current_user,
)

from app.modules.user.models import (
    User,
)

from app.modules.chat.schemas import (
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
    ChatMessageResponse,
)

from app.ai.agents.factory import get_orchestrator
from app.ai.memory.repository import ConversationRepository
from app.ai.memory.service import ConversationMemoryService

from app.modules.chat.service import ChatService
from app.modules.business.models import Business
from app.modules.membership.models import Membership
from app.shared.security.business import get_business_membership, require_business_member


router = APIRouter(
    prefix="/businesses/{business_id}/chat",
    tags=["Chat"],
    dependencies=[Depends(require_business_member)],
)


def _memory_service(db: Session) -> ConversationMemoryService:
    return ConversationMemoryService(
        repository=ConversationRepository(db=db),
    )


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    business_id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    """
    Ask a question about a business knowledge base.

    Routes to the appropriate AI agent via the Orchestrator.
    If `session_id` is omitted, a new conversation is started.
    """

    business = (
        db.query(Business)
        .filter(
            Business.id == business_id,
            Business.is_deleted.is_(False),
        )
        .first()
    )

    business_name = business.name if business else ""

    orchestrator = get_orchestrator(
        db=db,
        business_id=business_id,
        user_id=current_user.id,
        role=membership.role,
    )

    service = ChatService(
        orchestrator=orchestrator,
        memory_service=_memory_service(db),
    )

    return service.chat(
        business_id=business_id,
        user_id=current_user.id,
        request=request,
        business_name=business_name,
        role=membership.role,
    )


@router.get(
    "/sessions",
    response_model=list[ChatSessionResponse],
)
def list_sessions(
    business_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all of the current user's conversation sessions in this business,
    most recently active first.
    """

    return _memory_service(db).list_sessions(
        business_id=business_id,
        user_id=current_user.id,
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
def get_session_messages(
    business_id: UUID,
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the full message history of a specific conversation session.
    """

    memory_service = _memory_service(db)

    # Ownership check - raises NotFoundException if session doesn't
    # belong to this business/user.
    memory_service.get_or_create_session(
        business_id=business_id,
        user_id=current_user.id,
        session_id=session_id,
    )

    return memory_service.get_messages(session_id=session_id)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    business_id: UUID,
    session_id: UUID,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete (soft) a conversation session.
    """

    _memory_service(db).delete_session(
        business_id=business_id,
        user_id=current_user.id,
        session_id=session_id,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
