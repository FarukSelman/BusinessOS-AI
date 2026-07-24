from uuid import UUID

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import Base
from app.shared.models.base import BaseModel


class ConversationSession(BaseModel, Base):
    """
    Represents a conversation session.
    """

    __tablename__ = "conversation_sessions"

    business_id: Mapped[UUID] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )


    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
    ) 