from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import date, time
from uuid import UUID

class PublicServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str] = None
    price: float
    duration: int

class PublicBusinessInfo(BaseModel):
    id: UUID
    name: str
    slug: str
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    services: List[PublicServiceResponse] = []

class PublicAvailableSlots(BaseModel):
    date: date
    service_id: UUID
    available_slots: List[time]

class PublicBookingCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: Optional[EmailStr] = None
    service_id: UUID
    branch_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    date: date
    start_time: time

class PublicBookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    service_id: UUID
    branch_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    customer_id: UUID
    date: date
    start_time: time
    end_time: time
    status: str
