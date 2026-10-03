from uuid import UUID

from pydantic import BaseModel


class DocumentChunkSearchResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    score: float

    class Config:
        from_attributes = True