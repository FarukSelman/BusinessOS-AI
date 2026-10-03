from uuid import UUID

from app.ai.memory.repository import (
    ConversationRepository,
)

from app.ai.memory.schemas import (
    ConversationHistory,
)

from app.ai.memory.models.conversation_session import (
    ConversationSession,
)

from app.ai.memory.models.conversation_message import (
    ConversationMessage,
)


class ConversationMemoryService:
    """
    Service responsible for conversation memory management.
    """

    def __init__(
        self,
        repository: ConversationRepository,
    ):
        self.repository = repository

    def list_sessions(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
    ) -> list[ConversationSession]:
        return self.repository.list_sessions(
            business_id=business_id,
            user_id=user_id,
        )

    def get_or_create_session(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
        session_id: UUID | None = None,
    ) -> ConversationSession:
        return self.repository.get_or_create_session(
            business_id=business_id,
            user_id=user_id,
            session_id=session_id,
        )

    def get_history(
        self,
        *,
        session_id: UUID,
    ) -> ConversationHistory:
        return self.repository.get_history(
            session_id=session_id,
        )

    def get_messages(
        self,
        *,
        session_id: UUID,
    ) -> list[ConversationMessage]:
        return self.repository.get_messages(
            session_id=session_id,
        )

    def save_user_message(
        self,
        *,
        session_id: UUID,
        message: str,
    ) -> None:
        self.repository.save_message(
            session_id=session_id,
            role="user",
            content=message,
        )

    def save_assistant_message(
        self,
        *,
        session_id: UUID,
        message: str,
    ) -> None:
        self.repository.save_message(
            session_id=session_id,
            role="assistant",
            content=message,
        )

    def delete_session(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
        session_id: UUID,
    ) -> None:
        self.repository.delete_session(
            business_id=business_id,
            user_id=user_id,
            session_id=session_id,
        )