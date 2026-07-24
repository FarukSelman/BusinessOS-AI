from uuid import UUID

from app.ai.memory.repository import (
    ConversationRepository,
)

from app.ai.memory.schemas import (
    ConversationHistory,
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

    def get_session(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
    ):
        """
        Get current conversation session.
        """

        return self.repository.get_or_create_session(
            business_id=business_id,
            user_id=user_id,
        )


    def get_history(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
    ) -> ConversationHistory:
        """
        Retrieve previous conversation history.
        """

        return self.repository.get_history(
            business_id=business_id,
            user_id=user_id,
        )


    def save_user_message(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
        message: str,
    ) -> None:
        """
        Save user message.
        """

        self.repository.save_message(
            business_id=business_id,
            user_id=user_id,
            role="user",
            content=message,
        )


    def save_assistant_message(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
        message: str,
    ) -> None:
        """
        Save assistant response.
        """

        self.repository.save_message(
            business_id=business_id,
            user_id=user_id,
            role="assistant",
            content=message,
        )