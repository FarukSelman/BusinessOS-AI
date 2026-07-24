from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class ConversationSessionResponse(BaseModel):
    id: UUID

    business_id: UUID

    user_id: UUID

    title: str | None

    created_at: datetime

    updated_at: datetime


    class Config:
        from_attributes = True



class ConversationMessageResponse(BaseModel):

    id: UUID

    conversation_id: UUID

    role: str

    content: str

    created_at: datetime


    class Config:
        from_attributes = True