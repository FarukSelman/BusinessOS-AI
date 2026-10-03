import uuid
from typing import TYPE_CHECKING
from datetime import date, time

from sqlalchemy import Enum, String, Text, Date, Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel
from app.shared.enums.appointment import AppointmentStatus

if TYPE_CHECKING:
    from app.modules.customers.models import Customer
    from app.modules.services.models import Service

class Appointment(BaseModel):
    __tablename__ = "appointments"

    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    service_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("services.id"), nullable=True)
    staff_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("staff_profiles.id", ondelete="SET NULL"), nullable=True)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    customer_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
