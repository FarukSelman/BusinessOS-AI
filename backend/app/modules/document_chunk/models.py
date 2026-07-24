from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.shared.models.base import BaseModel
from app.shared.enums.document_chunk import EmbeddingStatus
from pgvector.sqlalchemy import Vector

if TYPE_CHECKING:
    from app.modules.document.models import Document


class DocumentChunk(BaseModel):

    __tablename__ = "document_chunks"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    token_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    embedding_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        Enum(
            EmbeddingStatus,
            name="embedding_status",
        ),
        default=EmbeddingStatus.PENDING,
        nullable=False,
    )
    embedding: Mapped[list[float] | None] = mapped_column(
    Vector(1536),
    nullable=True,
    )

    document: Mapped["Document"] = relationship(
        back_populates="chunks",
    )