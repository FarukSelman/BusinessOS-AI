from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: UUID | None = None


class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str
    agent_name: str | None = None
    tools_used: list[str] | None = None
    pending_actions: list[dict] | None = None


class ChatSessionResponse(BaseModel):
    id: UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
