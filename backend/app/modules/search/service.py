"""
Global search (Ctrl+K) across customers, appointments, invoices and products.

One request returns a few hits per type plus each type's total, using the
shared Turkish-insensitive text search, so the palette needs a single call per
keystroke and every type matches the same way.
"""
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import case, nulls_last, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.appointments.models import Appointment
from app.modules.customers.models import Customer
from app.modules.invoice.models import Invoice
from app.modules.products.models import Product
from app.modules.search.schemas import (
    AppointmentHit,
    CustomerHit,
    InvoiceHit,
    ProductHit,
    SearchGroup,
    SearchResponse,
)
from app.shared.utils.search import count_rows, text_search

LIMIT_PER_TYPE = 5


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def _group(self, statement, order_by, limit: int):
        total = count_rows(self.db, statement)
        rows = list(self.db.scalars(statement.order_by(*order_by).limit(limit)).all()) if total else []
        return total, rows

    def search(self, business_id: UUID, query: str, show_amounts: bool, limit: int = LIMIT_PER_TYPE) -> SearchResponse:
        def scoped(model):
            return select(model).where(model.business_id == business_id, model.is_deleted.is_(False))

        # Customers: name, e-mail, phone (digits)
        total, rows = self._group(
            scoped(Customer).where(text_search(query, Customer.name, Customer.email, phone_columns=(Customer.phone,))),
            (Customer.name, Customer.id),
            limit,
        )
        customers = SearchGroup[CustomerHit](
            total=total, items=[CustomerHit(id=c.id, name=c.name, phone=c.phone, email=c.email) for c in rows]
        )

        # Appointments: upcoming first (soonest first), then past (most recent first)
        today = datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date()
        upcoming = Appointment.appointment_date >= today
        total, rows = self._group(
            scoped(Appointment).where(
                text_search(query, Appointment.customer_name, Appointment.customer_email,
                            phone_columns=(Appointment.customer_phone,))
            ),
            (
                case((upcoming, 0), else_=1),
                nulls_last(case((upcoming, Appointment.appointment_date)).asc()),
                nulls_last(case((~upcoming, Appointment.appointment_date)).desc()),
                Appointment.start_time,
                Appointment.id,
            ),
            limit,
        )
        appointments = SearchGroup[AppointmentHit](
            total=total,
            items=[
                AppointmentHit(id=a.id, customer_name=a.customer_name, appointment_date=a.appointment_date,
                               start_time=a.start_time, status=a.status)
                for a in rows
            ],
        )

        # Invoices: number, customer; amounts only for roles that may see money
        total, rows = self._group(
            scoped(Invoice).where(
                text_search(query, Invoice.invoice_number, Invoice.customer_name, Invoice.customer_email)
            ),
            (Invoice.created_at.desc(), Invoice.id),
            limit,
        )
        invoices = SearchGroup[InvoiceHit](
            total=total,
            items=[
                InvoiceHit(id=i.id, invoice_number=i.invoice_number, customer_name=i.customer_name, status=i.status,
                           total_amount=float(i.total_amount) if show_amounts else None)
                for i in rows
            ],
        )

        # Products: name, SKU, barcode
        total, rows = self._group(
            scoped(Product).where(text_search(query, Product.name, Product.sku, Product.barcode)),
            (Product.name, Product.id),
            limit,
        )
        products = SearchGroup[ProductHit](
            total=total,
            items=[ProductHit(id=p.id, name=p.name, sku=p.sku, current_stock=p.current_stock) for p in rows],
        )

        return SearchResponse(
            query=query, customers=customers, appointments=appointments, invoices=invoices, products=products
        )
