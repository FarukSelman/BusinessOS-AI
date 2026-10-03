import uuid
from datetime import date, time, datetime
from pydantic import BaseModel, ConfigDict

from app.shared.enums.appointment import AppointmentStatus

class AppointmentCreate(BaseModel):
    customer_name: str
    customer_phone: str | None = None
    customer_email: str | None = None
    service_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    staff_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None
    appointment_date: date
    start_time: time
    end_time: time | None = None
    notes: str | None = None

class AppointmentUpdate(BaseModel):
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None
    service_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    staff_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None
    appointment_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    status: AppointmentStatus | None = None
    notes: str | None = None

class AppointmentResponse(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    customer_name: str
    customer_phone: str | None
    customer_email: str | None
    service_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    staff_id: uuid.UUID | None
    branch_id: uuid.UUID | None
    appointment_date: date
    start_time: time
    end_time: time | None
    status: AppointmentStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AvailableSlotResponse(BaseModel):
    date: date
    available_slots: list[str]
