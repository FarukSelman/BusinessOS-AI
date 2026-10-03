from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.enums.reminder import ReminderChannel, ReminderStatus

MAX_HOURS_BEFORE = 168  # 7 days


def _email_only(channel: ReminderChannel | None) -> ReminderChannel | None:
    if channel == ReminderChannel.SMS:
        raise ValueError("SMS hatırlatmaları henüz desteklenmiyor; yalnızca EMAIL kullanılabilir.")
    return channel


class ReminderConfigCreate(BaseModel):
    channel: ReminderChannel = ReminderChannel.EMAIL
    hours_before: int = Field(..., ge=1, le=MAX_HOURS_BEFORE, description="Randevudan kaç saat önce (1-168)")
    message_template: str = Field(..., min_length=1, max_length=2000)
    is_active: bool = True

    _channel = field_validator("channel")(_email_only)

    @field_validator("message_template")
    @classmethod
    def strip_template(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Mesaj şablonu boş olamaz.")
        return value


class ReminderConfigUpdate(BaseModel):
    channel: Optional[ReminderChannel] = None
    hours_before: Optional[int] = Field(None, ge=1, le=MAX_HOURS_BEFORE)
    message_template: Optional[str] = Field(None, min_length=1, max_length=2000)
    is_active: Optional[bool] = None

    _channel = field_validator("channel")(_email_only)

    @field_validator("message_template")
    @classmethod
    def strip_template(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Mesaj şablonu boş olamaz.")
        return value


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
    appointment_start: datetime
    recipient_email: Optional[str] = None
    attempts: int = 0
    sent_at: Optional[datetime] = None
    status: ReminderStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Filled from the joined appointment / config for the history list.
    customer_name: Optional[str] = None
    hours_before: Optional[int] = None


class TestReminderResponse(BaseModel):
    status: str
    recipient: str
