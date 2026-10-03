import uuid
from typing import TYPE_CHECKING
from datetime import date, datetime

from sqlalchemy import Enum, String, Text, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel
from app.shared.enums.invoice import InvoiceStatus, PaymentMethod

if TYPE_CHECKING:
    from app.modules.customers.models import Customer
    from app.modules.appointments.models import Appointment

class Invoice(BaseModel):
    __tablename__ = "invoices"

    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True)
    
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    items: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(Enum(PaymentMethod), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
