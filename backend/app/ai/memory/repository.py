from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.memory.models.conversation_session import (
    ConversationSession,
)

from app.ai.memory.models.conversation_message import (
    ConversationMessage,
)

from app.ai.memory.schemas import (
    ConversationHistory,
    ChatMessage,
)

from app.ai.memory.enums import (
    MessageRole,
)


class ConversationRepository:
    """
    PostgreSQL repository for conversation memory.
    """


    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_sessions(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
    ) -> list[ConversationSession]:
        """
        Get all conversation sessions for user.
        """

        sessions = (
            self.db.query(
                ConversationSession
            )
            .filter(
                ConversationSession.business_id == business_id,
                ConversationSession.user_id == user_id,
                ConversationSession.is_deleted.is_(False),
            )
            .order_by(
                ConversationSession.updated_at.desc()
            )
            .all()
        )

        return sessions



    def get_or_create_session(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
    ) -> ConversationSession:
        """
        Get existing conversation session.
        If not exists create one.
        """


        session = (
            self.db.query(
                ConversationSession
            )
            .filter(
                ConversationSession.business_id == business_id,
                ConversationSession.user_id == user_id,
                ConversationSession.is_deleted.is_(False),
            )
            .first()
        )


        if session:
            return session



        session = ConversationSession(
            business_id=business_id,
            user_id=user_id,
            title="Chat Session",
        )


        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)


        return session



    def get_history(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
    ) -> ConversationHistory:
        """
        Load previous messages.
        """


        session = self.get_or_create_session(
            business_id=business_id,
            user_id=user_id,
        )


        messages = (
            self.db.query(
                ConversationMessage
            )
            .filter(
                ConversationMessage.conversation_id == session.id,
                ConversationMessage.is_deleted.is_(False),
            )
            .order_by(
                ConversationMessage.created_at.desc()
            )
            .limit(10)
            .all()
        )


        messages.reverse()



        return ConversationHistory(
            messages=[
                ChatMessage(
                    role=message.role.value,
                    content=message.content,
                )
                for message in messages
            ]
        )



    def save_message(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
        role: str,
        content: str,
    ) -> None:
        """
        Save new message.
        """


        session = self.get_or_create_session(
            business_id=business_id,
            user_id=user_id,
        )


        message = ConversationMessage(
            conversation_id=session.id,
            role=MessageRole[role.upper()],
            content=content,
        )


        self.db.add(message)
        self.db.commit()