from sqlalchemy.orm import Session

from app.ai.memory.repository import ConversationRepository
from app.ai.memory.service import ConversationMemoryService


def get_memory_service(
    db: Session,
) -> ConversationMemoryService:

    repository = ConversationRepository(
        db,
    )

    return ConversationMemoryService(
        repository=repository,
    )