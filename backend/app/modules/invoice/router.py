from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.invoice.repository import InvoiceRepository
from app.modules.invoice.schemas import (
    InvoiceCreatePayload,
    InvoiceUpdatePayload,
    InvoiceResponse,
    InvoiceStatsResponse,
    invoice_view,
)
from app.modules.invoice.service import InvoiceService
from app.modules.appointments.repository import AppointmentRepository
from app.shared.enums.invoice import InvoiceStatus, PaymentMethod
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.ai.agents.tools.common import can_view_finance
from app.modules.membership.models import Membership
from app.shared.security.business import get_business_membership, require_business_member, require_finance

# Reading: every member sees invoices, but only finance roles (owner, admin) see
# amounts. Writing (create, edit, pay, cancel) is for finance roles only.
router = APIRouter(
    prefix="/businesses/{business_id}/invoices",
    tags=["Invoices"],
    dependencies=[Depends(require_business_member)],
)

def get_service(db: Session = Depends(get_db)) -> InvoiceService:
    repository = InvoiceRepository(db)
    uow = UnitOfWork(db)
    appointment_repo = AppointmentRepository(db)
    return InvoiceService(repository=repository, uow=uow, appointment_repo=appointment_repo)

@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invoice",
)
def create_invoice(
    business_id: UUID,
    payload: InvoiceCreatePayload,
    service: InvoiceService = Depends(get_service),
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    return service.create_invoice(business_id, payload)

@router.get(
    "",
    response_model=list[InvoiceResponse],
    summary="List invoices",
)
def list_invoices(
    business_id: UUID,
    response: Response,
    status_filter: InvoiceStatus | None = Query(None, alias="status"),
    search: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    service: InvoiceService = Depends(get_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    invoices, total = service.list_invoices(business_id, status_filter, page, size, search)
    response.headers["X-Total-Count"] = str(total)
    show = can_view_finance(membership.role)
    return [invoice_view(inv, show) for inv in invoices]

@router.get(
    "/stats",
    response_model=InvoiceStatsResponse,
    summary="Revenue statistics",
)
def get_revenue_stats(
    business_id: UUID,
    service: InvoiceService = Depends(get_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    stats = service.get_revenue_stats(business_id)
    if not can_view_finance(membership.role):
        stats = {**stats, "total_revenue": None}  # counts stay, money goes
    return stats

@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice",
)
def get_invoice(
    business_id: UUID,
    invoice_id: UUID,
    service: InvoiceService = Depends(get_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    return invoice_view(service.get_invoice(business_id, invoice_id), can_view_finance(membership.role))

@router.patch(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Update invoice",
)
def update_invoice(
    business_id: UUID,
    invoice_id: UUID,
    payload: InvoiceUpdatePayload,
    service: InvoiceService = Depends(get_service),
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    return service.update_invoice(business_id, invoice_id, payload)

@router.post(
    "/{invoice_id}/pay",
    response_model=InvoiceResponse,
    summary="Mark as paid",
)
def mark_as_paid(
    business_id: UUID,
    invoice_id: UUID,
    payment_method: PaymentMethod = Query(...),
    service: InvoiceService = Depends(get_service),
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    return service.mark_as_paid(business_id, invoice_id, payment_method)

@router.post(
    "/{invoice_id}/cancel",
    response_model=InvoiceResponse,
    summary="Cancel invoice",
)
def cancel_invoice(
    business_id: UUID,
    invoice_id: UUID,
    service: InvoiceService = Depends(get_service),
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    return service.cancel_invoice(business_id, invoice_id)

@router.post(
    "/from-appointment/{appointment_id}",
    response_model=InvoiceResponse,
    summary="Create from appointment",
)
def create_from_appointment(
    business_id: UUID,
    appointment_id: UUID,
    service: InvoiceService = Depends(get_service),
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    return service.create_from_appointment(business_id, appointment_id)
