from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str