import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.shared.enums.invoice import InvoiceStatus, PaymentMethod

class InvoiceItemSchema(BaseModel):
    description: str
    quantity: int
    unit_price: float
    total: float

class InvoiceCreatePayload(BaseModel):
    customer_id: uuid.UUID | None = None
    customer_name: str
    customer_email: str | None = None
    appointment_id: uuid.UUID | None = None
    items: list[InvoiceItemSchema]
    subtotal: float
    tax_rate: float = 0.0
    tax_amount: float
    total_amount: float
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: date | None = None
    notes: str | None = None

class InvoiceUpdatePayload(BaseModel):
    customer_id: uuid.UUID | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    items: list[InvoiceItemSchema] | None = None
    subtotal: float | None = None
    tax_rate: float | None = None
    tax_amount: float | None = None
    total_amount: float | None = None
    status: InvoiceStatus | None = None
    due_date: date | None = None
    notes: str | None = None

class InvoiceResponse(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    customer_id: uuid.UUID | None
    customer_name: str
    customer_email: str | None
    appointment_id: uuid.UUID | None
    invoice_number: str
    items: list[InvoiceItemSchema]
    subtotal: float
    tax_rate: float
    tax_amount: float
    total_amount: float
    status: InvoiceStatus
    payment_method: PaymentMethod | None
    paid_at: datetime | None
    due_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int
