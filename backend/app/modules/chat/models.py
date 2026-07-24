from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    Enum,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.shared.models.base import BaseModel
from app.shared.enums.chat import MessageRole


class ConversationSession(BaseModel):

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


    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )



class ConversationMessage(BaseModel):

    __tablename__ = "conversation_messages"


    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversation_sessions.id"),
        nullable=False,
        index=True,
    )


    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            name="message_role",
        ),
        nullable=False,
    )


    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    conversation: Mapped["ConversationSession"] = relationship(
        back_populates="messages",
    )