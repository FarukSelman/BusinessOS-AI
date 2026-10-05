"""
Public online booking API (/public/booking/{slug}/...). No login.

Every endpoint is rate limited per IP; responses use the explicit public
schemas in schemas.py so no internal data (staff contact details, customer
records, user ids) leaves the server.
"""
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.appointments.dependencies import build_appointment_service
from app.modules.appointments.repository import AppointmentRepository
from app.modules.business.repository import BusinessRepository
from app.modules.customers.repository import CustomerRepository
from app.modules.public_booking.notify import build_customer_email, notify_business, send_customer_email
from app.modules.public_booking.schemas import (
    PublicAvailableSlots,
    PublicBookingCreate,
    PublicBookingResponse,
    PublicBranchResponse,
    PublicBusinessInfo,
    PublicOpeningHours,
    PublicServiceResponse,
    PublicStaffResponse,
    PublicStaffService,
)
from app.modules.public_booking.service import PublicBookingService
from app.modules.services.repository import ServiceRepository
from app.shared.security.rate_limit import rate_limit

query_limit = Depends(rate_limit("public-query", "PUBLIC_QUERY_LIMIT", "PUBLIC_QUERY_WINDOW_SECONDS"))
booking_limit = Depends(rate_limit("public-book", "PUBLIC_BOOKING_LIMIT", "PUBLIC_BOOKING_WINDOW_SECONDS"))

router = APIRouter(prefix="/public/booking/{business_slug}", tags=["Public Booking"])


def get_service(db: Session = Depends(get_db)) -> PublicBookingService:
    return PublicBookingService(
        business_repo=BusinessRepository(db),
        service_repo=ServiceRepository(db),
        appointment_repo=AppointmentRepository(db),
        customer_repo=CustomerRepository(db),
        appointment_service=build_appointment_service(db),
        uow=UnitOfWork(db),
    )


def _public_service(s) -> PublicServiceResponse:
    return PublicServiceResponse(
        id=s.id,
        name=s.name,
        description=s.description,
        price=float(s.price) if s.price else 0,
        duration=s.duration_minutes or 30,
    )


@router.get("/info", response_model=PublicBusinessInfo, dependencies=[query_limit])
def get_business_info(business_slug: str, service: PublicBookingService = Depends(get_service)):
    business = service.get_business_by_slug(business_slug)
    return PublicBusinessInfo(
        id=business.id,
        name=business.name,
        slug=business.slug,
        industry=business.industry,
        logo_url=business.logo_url,
        description=None,
        phone=business.phone,
        website=business.website,
        address=service.main_address(business.id),
        opening_hours=[PublicOpeningHours(**day) for day in service.opening_hours(business.id)],
        services=[_public_service(s) for s in service.list_public_services(business.id)],
    )


@router.get("/services", response_model=List[PublicServiceResponse], dependencies=[query_limit])
def list_services(business_slug: str, service: PublicBookingService = Depends(get_service)):
    business = service.get_business_by_slug(business_slug)
    return [_public_service(s) for s in service.list_public_services(business.id)]


@router.get("/branches", response_model=List[PublicBranchResponse], dependencies=[query_limit])
def list_branches(business_slug: str, service: PublicBookingService = Depends(get_service)):
    business = service.get_business_by_slug(business_slug)
    return [
        PublicBranchResponse(id=b.id, name=b.name, address=b.address, phone=b.phone, is_main=bool(b.is_main))
        for b in service.list_branches(business.id)
    ]


@router.get("/staff", response_model=List[PublicStaffResponse], dependencies=[query_limit])
def list_staff(
    business_slug: str,
    service_id: Optional[UUID] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    service: PublicBookingService = Depends(get_service),
):
    business = service.get_business_by_slug(business_slug)
    staff = service.eligible_staff(business.id, service_id, branch_id)
    offered = service.staff_services([s.id for s in staff])
    return [
        PublicStaffResponse(
            id=s.id,
            full_name=s.full_name,
            title=s.title,
            bio=s.bio,
            avatar_url=s.avatar_url,
            branch_id=s.branch_id,
            services=[PublicStaffService(id=x.id, name=x.name) for x in offered.get(s.id, [])],
        )
        for s in staff
    ]


@router.get("/available-slots", response_model=PublicAvailableSlots, dependencies=[query_limit])
def get_available_slots(
    business_slug: str,
    date: date,
    service_id: UUID,
    staff_id: Optional[UUID] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    service: PublicBookingService = Depends(get_service),
):
    business = service.get_business_by_slug(business_slug)
    slots = service.get_available_slots(business.id, date, service_id, staff_id, branch_id)
    return PublicAvailableSlots(date=date, service_id=service_id, available_slots=slots)


@router.post(
    "/book",
    response_model=PublicBookingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[booking_limit],
)
def book_appointment(
    business_slug: str,
    data: PublicBookingCreate,
    background: BackgroundTasks,
    service: PublicBookingService = Depends(get_service),
    db: Session = Depends(get_db),
):
    result = service.create_public_booking(
        business_slug, data, max_open_per_phone=settings.PUBLIC_BOOKING_MAX_OPEN_PER_PHONE or None,
    )
    appointment = result.appointment

    # The booking is already committed; messages must not undo or fail it.
    try:
        notify_business(db, result)
    except Exception:
        db.rollback()
    if appointment.customer_email:
        subject, html_body, text_body = build_customer_email(result)
        background.add_task(send_customer_email, appointment.customer_email, subject, html_body, text_body)

    return PublicBookingResponse(
        id=appointment.id,
        business_id=appointment.business_id,
        service_id=appointment.service_id,
        branch_id=appointment.branch_id,
        staff_id=appointment.staff_id,
        staff_name=result.staff.full_name if result.staff else None,
        customer_id=appointment.customer_id,
        date=appointment.appointment_date,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        status=getattr(appointment.status, "value", appointment.status),
    )
