from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.ai.rag.factory import get_rag_service

from app.ai.memory.repository import (
    ConversationRepository,
)

from app.ai.memory.service import (
    ConversationMemoryService,
)

from app.modules.chat.service import ChatService



def get_chat_service(
    db: Session = Depends(get_db),
) -> ChatService:
    """
    Dependency that provides ChatService.
    """


    rag_service = get_rag_service(
        db,
    )


    memory_repository = ConversationRepository(
        db=db,
    )


    memory_service = ConversationMemoryService(
        repository=memory_repository,
    )


    return ChatService(
        rag_service=rag_service,
        memory_service=memory_service,
    )

def get_memory_service(
    db: Session = Depends(get_db),
) -> ConversationMemoryService:

    repository = ConversationRepository(
        db=db,
    )

    return ConversationMemoryService(
        repository=repository,
    )