from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException

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

    def list_sessions(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
    ) -> list[ConversationSession]:
        """
        List all conversation sessions for a user in a business,
        most recently updated first.
        """

        return (
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

    def get_or_create_session(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
        session_id: UUID | None = None,
    ) -> ConversationSession:
        """
        If session_id is given, fetch that exact session (must belong
        to this business + user). If session_id is None, a brand new
        session is created - this is what starts a fresh conversation.
        """

        if session_id is not None:
            session = (
                self.db.query(
                    ConversationSession
                )
                .filter(
                    ConversationSession.id == session_id,
                    ConversationSession.business_id == business_id,
                    ConversationSession.user_id == user_id,
                    ConversationSession.is_deleted.is_(False),
                )
                .first()
            )

            if not session:
                raise NotFoundException("Conversation session not found.")

            return session

        session = ConversationSession(
            business_id=business_id,
            user_id=user_id,
            title=None,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def get_history(
        self,
        *,
        session_id: UUID,
    ) -> ConversationHistory:
        """
        Load previous messages for a specific session (for LLM context).
        """

        messages = (
            self.db.query(
                ConversationMessage
            )
            .filter(
                ConversationMessage.conversation_id == session_id,
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

    def get_messages(
        self,
        *,
        session_id: UUID,
    ) -> list[ConversationMessage]:
        """
        Load the full message list for a session (for displaying
        a past conversation in the UI).
        """

        return (
            self.db.query(
                ConversationMessage
            )
            .filter(
                ConversationMessage.conversation_id == session_id,
                ConversationMessage.is_deleted.is_(False),
            )
            .order_by(
                ConversationMessage.created_at.asc()
            )
            .all()
        )

    def save_message(
        self,
        *,
        session_id: UUID,
        role: str,
        content: str,
    ) -> None:
        """
        Save a new message onto a specific session, and auto-title
        the session from the first user message if it has no title yet.
        """

        message = ConversationMessage(
            conversation_id=session_id,
            role=MessageRole[role.upper()],
            content=content,
        )

        self.db.add(message)

        if role.upper() == "USER":
            session = (
                self.db.query(ConversationSession)
                .filter(ConversationSession.id == session_id)
                .first()
            )
            if session and not session.title:
                session.title = content[:50]

        self.db.commit()

    def delete_session(
        self,
        *,
        business_id: UUID,
        user_id: UUID,
        session_id: UUID,
    ) -> None:
        session = self.get_or_create_session(
            business_id=business_id,
            user_id=user_id,
            session_id=session_id,
        )
        session.is_deleted = True
        self.db.commit()