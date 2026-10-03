from datetime import date, time
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.staff.repository import StaffProfileRepository, StaffServiceRepository, StaffScheduleRepository
from app.modules.staff.schemas import StaffCreate, StaffUpdate, StaffResponse, StaffServiceAssign, StaffScheduleSet, StaffScheduleResponse, ServiceBasic
from app.modules.staff.service import StaffServiceDomain
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.shared.security.business import require_business_member

router = APIRouter(prefix="/businesses/{business_id}/staff", tags=["Staff"], dependencies=[Depends(require_business_member)])

def get_service(db: Session = Depends(get_db)) -> StaffServiceDomain:
    profile_repo = StaffProfileRepository(db)
    service_repo = StaffServiceRepository(db)
    schedule_repo = StaffScheduleRepository(db)
    uow = UnitOfWork(db)
    return StaffServiceDomain(
        profile_repo=profile_repo, 
        service_repo=service_repo,
        schedule_repo=schedule_repo,
        uow=uow
    )

@router.get("/available", response_model=list[StaffResponse])
def get_available_staff(
    business_id: UUID,
    date: date,
    start_time: time,
    service_id: UUID,
    branch_id: UUID | None = None,
    service: StaffServiceDomain = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    staff_list = service.get_available_staff_for_slot(
        business_id=business_id,
        date_obj=date,
        start_time=start_time,
        service_id=service_id,
        branch_id=branch_id
    )
    return [service._enrich_staff(s) for s in staff_list]

@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    business_id: UUID,
    data: StaffCreate,
    service: StaffServiceDomain = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.create_staff(business_id=business_id, data=data)

@router.get("", response_model=list[StaffResponse])
def list_staff(
    business_id: UUID,
    branch_id: UUID | None = None,
    page: int = 1,
    size: int = 20,
    service: StaffServiceDomain = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_staff(business_id=business_id, branch_id=branch_id, page=page, size=size)

@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff(
    business_id: UUID,
    staff_id: UUID,
    service: StaffServiceDomain = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_staff(business_id=business_id, staff_id=staff_id)

@router.patch("/{staff_id}", response_model=StaffResponse)
def update_staff(
    business_id: UUID,
    staff_id: UUID,
    data: StaffUpdate,
    service: StaffServiceDomain = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.update_staff(business_id=business_id, staff_id=staff_id, data=data)

@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    business_id: UUID,
    staff_id: UUID,
    service: StaffServiceDomain = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    service.delete_staff(business_id=business_id, staff_id=staff_id)

@router.put("/{staff_id}/services", response_model=StaffResponse)
def assign_services(
    business_id: UUID,
    staff_id: UUID,
    data: StaffServiceAssign,
    service: StaffServiceDomain = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.assign_services(business_id=business_id, staff_id=staff_id, service_ids=data.service_ids)

@router.get("/{staff_id}/services", response_model=list[ServiceBasic])
def list_staff_services(
    business_id: UUID,
    staff_id: UUID,
    service: StaffServiceDomain = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_staff_services(staff_id=staff_id)

@router.put("/{staff_id}/schedule", response_model=list[StaffScheduleResponse])
def set_schedule(
    business_id: UUID,
    staff_id: UUID,
    data: StaffScheduleSet,
    service: StaffServiceDomain = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.set_schedule(business_id=business_id, staff_id=staff_id, data=data)

@router.get("/{staff_id}/schedule", response_model=list[StaffScheduleResponse])
def get_schedule(
    business_id: UUID,
    staff_id: UUID,
    service: StaffServiceDomain = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_schedule(staff_id=staff_id)
