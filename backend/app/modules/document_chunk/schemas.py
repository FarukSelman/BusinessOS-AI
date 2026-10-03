from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.shared.enums.document_chunk import EmbeddingStatus


class DocumentChunkResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )


    id: UUID

    document_id: UUID

    chunk_index: int

    content: str

    token_count: int | None

    embedding_model: str | None

    embedding_status: EmbeddingStatus

    created_at: datetime

    updated_at: datetime