from uuid import UUID

from app.modules.chat.repository import (
    ConversationRepository,
)

from app.shared.enums.chat import (
    MessageRole,
)


class ConversationMemoryService:
    """
    Handles conversation history management.
    """

    def __init__(
        self,
        repository: ConversationRepository,
    ):
        self.repository = repository


    def create_conversation(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
    ):
        """
        Create new conversation.
        """

        return self.repository.create_session(
            business_id=business_id,
            user_id=user_id,
        )


    def save_user_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
    ):
        """
        Save user message.
        """

        return self.repository.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )


    def save_assistant_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
    ):
        """
        Save assistant response.
        """

        return self.repository.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
        )


    def get_history(
        self,
        *,
        conversation_id: UUID,
        limit: int = 10,
    ):
        """
        Get recent conversation history.
        """

        messages = self.repository.get_messages(
            conversation_id=conversation_id,
            limit=limit,
        )

        return list(
            reversed(messages)
        )