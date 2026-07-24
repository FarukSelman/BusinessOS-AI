from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.chat.models import (
    ConversationSession,
    ConversationMessage,
)


class ConversationRepository:
    """
    Repository responsible for conversation memory persistence.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db


    def create_session(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
    ) -> ConversationSession:
        """
        Create a new conversation session.
        """

        session = ConversationSession(
            business_id=business_id,
            user_id=user_id,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session


    def get_session(
        self,
        *,
        conversation_id: UUID,
    ) -> ConversationSession | None:
        """
        Get conversation by id.
        """

        statement = select(
            ConversationSession
        ).where(
            ConversationSession.id == conversation_id
        )

        return self.db.scalar(statement)


    def add_message(
        self,
        *,
        conversation_id: UUID,
        role,
        content: str,
    ) -> ConversationMessage:
        """
        Store a conversation message.
        """

        message = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return message


    def get_messages(
        self,
        *,
        conversation_id: UUID,
        limit: int = 10,
    ) -> list[ConversationMessage]:
        """
        Retrieve recent conversation messages.
        """

        statement = (
            select(ConversationMessage)
            .where(
                ConversationMessage.conversation_id
                == conversation_id
            )
            .order_by(
                ConversationMessage.created_at.desc()
            )
            .limit(limit)
        )

        return list(
            self.db.scalars(statement).all()
        )