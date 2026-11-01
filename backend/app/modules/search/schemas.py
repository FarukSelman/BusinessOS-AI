from datetime import date, time
from uuid import UUID

from pydantic import BaseModel

from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.invoice import InvoiceStatus


class CustomerHit(BaseModel):
    id: UUID
    name: str
    phone: str | None
    email: str | None


class AppointmentHit(BaseModel):
    id: UUID
    customer_name: str
    appointment_date: date
    start_time: time
    status: AppointmentStatus


class InvoiceHit(BaseModel):
    id: UUID
    invoice_number: str
    customer_name: str
    status: InvoiceStatus
    # None for roles that may not see money (employee, viewer).
    total_amount: float | None


class ProductHit(BaseModel):
    id: UUID
    name: str
    sku: str | None
    current_stock: int


class StaffHit(BaseModel):
    id: UUID
    full_name: str
    title: str | None
    phone: str | None


class SearchGroup[T](BaseModel):
    """At most `limit` hits plus how many records match in total."""

    total: int
    items: list[T]


class SearchResponse(BaseModel):
    query: str
    customers: SearchGroup[CustomerHit]
    appointments: SearchGroup[AppointmentHit]
    invoices: SearchGroup[InvoiceHit]
    products: SearchGroup[ProductHit]
    staff: SearchGroup[StaffHit]
