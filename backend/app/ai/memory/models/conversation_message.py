from uuid import UUID

from sqlalchemy import (
    Text,
    ForeignKey,
    Enum,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.shared.models.base import (
    Base,
    BaseModel,
)

from app.ai.memory.enums import MessageRole


class ConversationMessage(BaseModel, Base):

    __tablename__ = "conversation_messages"


    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "conversation_sessions.id"
        ),
        nullable=False,
        index=True,
    )


    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            name="message_role",
            native_enum=True,
        ),
        nullable=False,
    )


    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    conversation = relationship(
        "ConversationSession",
        back_populates="messages",
    ) 