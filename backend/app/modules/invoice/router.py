from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.invoice.repository import InvoiceRepository
from app.modules.invoice.schemas import (
    InvoiceCreatePayload,
    InvoiceUpdatePayload,
    InvoiceResponse,
    InvoiceListResponse,
)
from app.modules.invoice.service import InvoiceService
from app.modules.appointments.repository import AppointmentRepository
from app.shared.enums.invoice import InvoiceStatus, PaymentMethod
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.shared.security.business import require_business_member

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
):
    return service.create_invoice(business_id, payload)

@router.get(
    "",
    response_model=list[InvoiceResponse],
    summary="List invoices",
)
def list_invoices(
    business_id: UUID,
    status_filter: InvoiceStatus | None = Query(None, alias="status"),
    page: int = 1,
    size: int = 20,
    service: InvoiceService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    return service.list_invoices(business_id, status_filter, page, size)

@router.get(
    "/stats",
    summary="Revenue statistics",
)
def get_revenue_stats(
    business_id: UUID,
    service: InvoiceService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    return service.get_revenue_stats(business_id)

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
):
    return service.get_invoice(business_id, invoice_id)

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
):
    return service.create_from_appointment(business_id, appointment_id)
