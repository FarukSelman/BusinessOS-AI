from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING
from uuid import UUID

from app.shared.models.base import BaseModel
from app.shared.enums.document import DocumentStatus
from app.modules.document_chunk.models import DocumentChunk


if TYPE_CHECKING:
    from app.modules.business.models import Business
    from app.modules.user.models import User




class Document(BaseModel):
    """
    Uploaded business document.

    Documents are processed and indexed for the RAG Knowledge Base.
    """

    __tablename__ = "documents"

    business_id: Mapped[UUID] = mapped_column(
        ForeignKey("businesses.id"),
        nullable=False,
        index=True,
    )

    uploaded_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    original_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus,
            name="document_status",
        ),
        default=DocumentStatus.UPLOADING,
        nullable=False,
    )

    business: Mapped["Business"] = relationship(
        back_populates="documents",
    )

    uploader: Mapped["User"] = relationship(
        back_populates="documents",
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
    back_populates="document",
    cascade="all, delete-orphan",
    )  