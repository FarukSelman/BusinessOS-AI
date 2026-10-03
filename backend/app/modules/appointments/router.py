from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.schemas import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    AvailableSlotResponse,
)
from app.modules.appointments.service import AppointmentService
from app.modules.appointments.dependencies import build_appointment_service

from app.modules.user.models import User

from app.shared.security.dependencies import get_current_user
from app.shared.security.business import require_business_member


router = APIRouter(
    prefix="/businesses/{business_id}/appointments",
    tags=["Appointments"],
    dependencies=[Depends(require_business_member)],
)


# --------------------------------------------------
# Dependency
# --------------------------------------------------

def get_service(
    db: Session = Depends(get_db),
) -> AppointmentService:

    return build_appointment_service(db)


# --------------------------------------------------
# CREATE
# --------------------------------------------------

@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create appointment",
)
def create_appointment(
    business_id: UUID,

    data: AppointmentCreate,

    service: AppointmentService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.create(
        business_id,
        data=data,
    )


# --------------------------------------------------
# LIST
# --------------------------------------------------

@router.get(
    "",
    response_model=list[AppointmentResponse],
    summary="List appointments",
)
def list_appointments(
    business_id: UUID,

    target_date: date | None = Query(
        None,
        alias="date",
        description="Filter by date",
    ),

    staff_id: UUID | None = Query(None, description="Filter by staff"),
    branch_id: UUID | None = Query(None, description="Filter by branch"),

    page: int = 1,
    size: int = 20,

    service: AppointmentService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    if staff_id:
        return service.repository.list_by_staff(business_id, staff_id, target_date)
    if branch_id:
        return service.repository.list_by_branch(business_id, branch_id, target_date)

    if target_date:
        return service.list_by_date(
            business_id,
            target_date,
        )

    return service.list(
        business_id,
        page=page,
        size=size,
    )


# --------------------------------------------------
# AVAILABLE SLOTS
# --------------------------------------------------

@router.get(
    "/available-slots",
    response_model=AvailableSlotResponse,
    summary="Get available slots",
)
def get_available_slots(
    business_id: UUID,

    target_date: date = Query(
        ...,
        alias="date",
        description="Date to check",
    ),

    duration_minutes: int = Query(
        60,
        description="Duration in minutes",
    ),
    
    staff_id: UUID | None = Query(None, description="Filter by staff"),
    branch_id: UUID | None = Query(None, description="Filter by branch"),

    service: AppointmentService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    slots = service.get_available_slots(
        business_id,
        target_date,
        duration_minutes=duration_minutes,
        staff_id=staff_id,
        branch_id=branch_id,
    )

    return AvailableSlotResponse(
        date=target_date,
        available_slots=slots,
    )


# --------------------------------------------------
# GET
# --------------------------------------------------

@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Get appointment",
)
def get_appointment(
    business_id: UUID,
    appointment_id: UUID,

    service: AppointmentService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.get(
        business_id,
        appointment_id,
    )


# --------------------------------------------------
# UPDATE
# --------------------------------------------------

@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Update appointment",
)
def update_appointment(
    business_id: UUID,
    appointment_id: UUID,

    data: AppointmentUpdate,

    service: AppointmentService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.update(
        business_id,
        appointment_id,
        data=data,
    )


# --------------------------------------------------
# CANCEL
# --------------------------------------------------

@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    summary="Cancel appointment",
)
def cancel_appointment(
    business_id: UUID,
    appointment_id: UUID,

    service: AppointmentService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.cancel(
        business_id,
        appointment_id,
    )


# --------------------------------------------------
# COMPLETE
# --------------------------------------------------

@router.post(
    "/{appointment_id}/complete",
    response_model=AppointmentResponse,
    summary="Complete appointment",
)
def complete_appointment(
    business_id: UUID,
    appointment_id: UUID,

    service: AppointmentService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.complete(
        business_id,
        appointment_id,
    )
