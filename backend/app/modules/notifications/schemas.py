import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.shared.enums.notification import NotificationType

class NotificationResponse(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    user_id: uuid.UUID | None
    title: str
    message: str
    type: NotificationType
    is_read: bool
    reference_id: uuid.UUID | None
    reference_type: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int

class MarkReadPayload(BaseModel):
    # Depending on how it's used, could just be empty or contain multiple IDs. 
    # The requirement is just "MarkReadPayload".
    pass
