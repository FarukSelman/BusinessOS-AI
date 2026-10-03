from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.ai.agents.factory import get_orchestrator
from app.ai.memory.repository import ConversationRepository
from app.ai.memory.service import ConversationMemoryService

from app.modules.chat.service import ChatService


def get_chat_service(
    db: Session = Depends(get_db),
) -> ChatService:
    """
    Dependency injection for ChatService.
    """

    # Memory service
    memory_repository = ConversationRepository(db=db)
    memory_service = ConversationMemoryService(
        repository=memory_repository,
    )

    return ChatService(
        orchestrator=None,  # Will be set per-request
        memory_service=memory_service,
    )


def get_memory_service(
    db: Session = Depends(get_db),
) -> ConversationMemoryService:
    """
    Dependency injection for ConversationMemoryService.
    """

    repository = ConversationRepository(db=db)

    return ConversationMemoryService(
        repository=repository,
    )