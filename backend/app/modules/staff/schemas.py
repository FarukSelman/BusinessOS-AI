from datetime import datetime, time
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.shared.enums.staff import StaffStatus

class ServiceBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    price: float
    duration_minutes: int
    category: str | None

class StaffCreate(BaseModel):
    full_name: str = Field(..., max_length=150)
    phone: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=255)
    title: str | None = Field(None, max_length=100)
    bio: str | None = None
    branch_id: UUID | None = None
    user_id: UUID | None = None
    color: str | None = Field("#6366f1", max_length=7)
    status: StaffStatus = StaffStatus.ACTIVE
    avatar_url: str | None = None

class StaffUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=150)
    phone: str | None = Field(None, max_length=30)
    email: str | None = Field(None, max_length=255)
    title: str | None = Field(None, max_length=100)
    bio: str | None = None
    branch_id: UUID | None = None
    user_id: UUID | None = None
    color: str | None = Field(None, max_length=7)
    status: StaffStatus | None = None
    avatar_url: str | None = None

class StaffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    business_id: UUID
    branch_id: UUID | None
    user_id: UUID | None
    full_name: str
    phone: str | None
    email: str | None
    title: str | None
    bio: str | None
    avatar_url: str | None
    status: StaffStatus
    color: str
    services: list[ServiceBasic] = []
    created_at: datetime
    updated_at: datetime

class StaffServiceAssign(BaseModel):
    service_ids: list[UUID]

class StaffScheduleItem(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    is_working: bool = True

class StaffScheduleSet(BaseModel):
    items: list[StaffScheduleItem]

class StaffScheduleResponse(StaffScheduleItem):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    staff_id: UUID
    business_id: UUID
