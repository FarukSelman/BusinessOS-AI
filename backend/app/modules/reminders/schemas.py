from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.shared.enums.reminder import ReminderChannel, ReminderStatus

class ReminderConfigCreate(BaseModel):
    channel: ReminderChannel
    hours_before: int
    message_template: str
    is_active: bool = True

class ReminderConfigUpdate(BaseModel):
    channel: Optional[ReminderChannel] = None
    hours_before: Optional[int] = None
    message_template: Optional[str] = None
    is_active: Optional[bool] = None

class ReminderConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    business_id: UUID
    channel: ReminderChannel
    hours_before: int
    message_template: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ReminderLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    business_id: UUID
    appointment_id: UUID
    reminder_config_id: UUID
    channel: ReminderChannel
    sent_at: Optional[datetime] = None
    status: ReminderStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
