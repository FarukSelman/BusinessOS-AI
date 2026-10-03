import datetime
from uuid import UUID

from sqlalchemy import select

from app.core.exceptions import NotFoundException
from app.db.unit_of_work import UnitOfWork
from app.modules.invoice.models import Invoice
from app.modules.invoice.repository import InvoiceRepository
from app.modules.invoice.schemas import InvoiceCreatePayload, InvoiceUpdatePayload
from app.shared.enums.invoice import InvoiceStatus, PaymentMethod

from app.modules.appointments.repository import AppointmentRepository


class InvoiceService:
    def __init__(
        self,
        repository: InvoiceRepository,
        uow: UnitOfWork,
        appointment_repo: AppointmentRepository,
    ):
        self.repository = repository
        self.uow = uow
        self.appointment_repo = appointment_repo

    def create_invoice(self, business_id: UUID, payload: InvoiceCreatePayload) -> Invoice:
        # Auto-generate invoice_number: INV-YYYY-XXXX
        year = datetime.datetime.now(datetime.UTC).year
        # count existing invoices for this year to append index
        # For simplicity in this mock, we just generate a simple number.
        import random
        invoice_number = f"INV-{year}-{random.randint(1000, 9999)}"

        items_dict = [item.model_dump() for item in payload.items]

        invoice = Invoice(
            business_id=business_id,
            customer_id=payload.customer_id,
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            appointment_id=payload.appointment_id,
            invoice_number=invoice_number,
            items=items_dict,
            subtotal=payload.subtotal,
            tax_rate=payload.tax_rate,
            tax_amount=payload.tax_amount,
            total_amount=payload.total_amount,
            status=payload.status,
            due_date=payload.due_date,
            notes=payload.notes,
        )

        with self.uow:
            self.repository.create(invoice)
            self.uow.flush()
            self.uow.refresh(invoice)

        return invoice

    def list_invoices(
        self,
        business_id: UUID,
        status_filter: InvoiceStatus | None,
        page: int,
        size: int,
    ) -> list[Invoice]:
        return self.repository.get_by_business(
            business_id, status_filter=status_filter, page=page, size=size
        )

    def get_invoice(self, business_id: UUID, invoice_id: UUID) -> Invoice:
        invoice = self.repository.get(invoice_id)
        # An invoice of another business is reported as "not found" (no ID probing).
        if not invoice or invoice.business_id != business_id:
            raise NotFoundException("Invoice not found.")
        return invoice

    def update_invoice(self, business_id: UUID, invoice_id: UUID, payload: InvoiceUpdatePayload) -> Invoice:
        invoice = self.get_invoice(business_id, invoice_id)
        
        update_data = payload.model_dump(exclude_unset=True)
        if "items" in update_data and update_data["items"]:
            update_data["items"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in update_data["items"]]

        for key, value in update_data.items():
            setattr(invoice, key, value)

        with self.uow:
            self.uow.flush()
            self.uow.refresh(invoice)

        return invoice

    def mark_as_paid(self, business_id: UUID, invoice_id: UUID, payment_method: PaymentMethod) -> Invoice:
        invoice = self.get_invoice(business_id, invoice_id)
        
        invoice.status = InvoiceStatus.PAID
        invoice.payment_method = payment_method
        invoice.paid_at = datetime.datetime.now(datetime.UTC)

        with self.uow:
            self.uow.flush()
            self.uow.refresh(invoice)

        return invoice

    def cancel_invoice(self, business_id: UUID, invoice_id: UUID) -> Invoice:
        invoice = self.get_invoice(business_id, invoice_id)
        invoice.status = InvoiceStatus.CANCELLED

        with self.uow:
            self.uow.flush()
            self.uow.refresh(invoice)

        return invoice

    def get_revenue_stats(self, business_id: UUID) -> dict:
        return self.repository.get_revenue_stats(business_id)

    def create_from_appointment(self, business_id: UUID, appointment_id: UUID) -> Invoice:
        appointment = self.appointment_repo.get_by_business(business_id, appointment_id)
        if not appointment:
            raise NotFoundException("Appointment not found.")

        # For simplicity, default values for items and amounts are used
        payload = InvoiceCreatePayload(
            customer_id=appointment.customer_id,
            customer_name=appointment.customer_name,
            customer_email=appointment.customer_email,
            appointment_id=appointment.id,
            items=[{
                "description": f"Service for appointment {appointment_id}",
                "quantity": 1,
                "unit_price": 100.0,
                "total": 100.0
            }],
            subtotal=100.0,
            tax_rate=0.0,
            tax_amount=0.0,
            total_amount=100.0,
            status=InvoiceStatus.DRAFT,
        )
        return self.create_invoice(business_id, payload)
