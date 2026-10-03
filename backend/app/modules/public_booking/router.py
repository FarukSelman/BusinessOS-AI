from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
from typing import List, Dict
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.business.repository import BusinessRepository
from app.modules.services.repository import ServiceRepository
from app.modules.appointments.repository import AppointmentRepository
from app.modules.customers.repository import CustomerRepository
from app.modules.appointments.service import AppointmentService
from app.modules.appointments.dependencies import build_appointment_service
from app.modules.public_booking.schemas import PublicBusinessInfo, PublicServiceResponse, PublicAvailableSlots, PublicBookingCreate, PublicBookingResponse
from app.modules.public_booking.service import PublicBookingService
from app.modules.branches.schemas import BranchResponse
from app.modules.staff.schemas import StaffResponse
from app.modules.branches.repository import BranchRepository
from app.modules.staff.repository import StaffProfileRepository, StaffServiceRepository, StaffScheduleRepository
from app.modules.staff.service import StaffServiceDomain

router = APIRouter(prefix="/public/booking/{business_slug}", tags=["Public Booking"])

def get_service(db: Session = Depends(get_db)) -> PublicBookingService:
    business_repo = BusinessRepository(db)
    service_repo = ServiceRepository(db)
    appointment_repo = AppointmentRepository(db)
    customer_repo = CustomerRepository(db)
    uow = UnitOfWork(db)
    
    appointment_service = build_appointment_service(db)
    
    return PublicBookingService(
        business_repo=business_repo,
        service_repo=service_repo,
        appointment_repo=appointment_repo,
        customer_repo=customer_repo,
        appointment_service=appointment_service,
        uow=uow
    )

@router.get("/info", response_model=PublicBusinessInfo)
def get_business_info(
    business_slug: str, 
    service: PublicBookingService = Depends(get_service)
):
    business = service.get_business_by_slug(business_slug)
    # The response model requires services too, optionally
    services = service.list_public_services(business.id)
    
    return PublicBusinessInfo(
        id=business.id,
        name=business.name,
        slug=business.slug,
        industry=business.industry,
        logo_url=business.logo_url,
        description=None,
        services=[
            PublicServiceResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                price=float(s.price) if s.price else 0,
                duration=s.duration_minutes or 30
            ) for s in services
        ]
    )

@router.get("/services", response_model=List[PublicServiceResponse])
def list_services(
    business_slug: str, 
    service: PublicBookingService = Depends(get_service)
):
    business = service.get_business_by_slug(business_slug)
    services = service.list_public_services(business.id)
    return [
        PublicServiceResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            price=float(s.price) if s.price else 0,
            duration=s.duration_minutes or 30
        ) for s in services
    ]

@router.get("/branches", response_model=List[BranchResponse])
def list_branches(
    business_slug: str,
    service: PublicBookingService = Depends(get_service),
    db: Session = Depends(get_db)
):
    business = service.get_business_by_slug(business_slug)
    repo = BranchRepository(db)
    return repo.list_by_business(business.id, size=100)

@router.get("/staff", response_model=List[StaffResponse])
def list_staff(
    business_slug: str,
    service_id: UUID = Query(None),
    branch_id: UUID = Query(None),
    service: PublicBookingService = Depends(get_service),
    db: Session = Depends(get_db)
):
    business = service.get_business_by_slug(business_slug)
    
    profile_repo = StaffProfileRepository(db)
    service_repo = StaffServiceRepository(db)
    schedule_repo = StaffScheduleRepository(db)
    uow = UnitOfWork(db)
    staff_service = StaffServiceDomain(profile_repo, service_repo, schedule_repo, uow)
    
    if service_id:
        staff_list = staff_service.get_available_staff_for_slot(business.id, date.today(), None, service_id, branch_id)
        return [staff_service._enrich_staff(s) for s in staff_list]
    else:
        staff_list = profile_repo.list_active(business.id, branch_id)
        return [staff_service._enrich_staff(s) for s in staff_list]

@router.get("/available-slots", response_model=PublicAvailableSlots)
def get_available_slots(
    business_slug: str,
    date: date,
    service_id: UUID,
    staff_id: UUID = Query(None),
    branch_id: UUID = Query(None),
    service: PublicBookingService = Depends(get_service)
):
    business = service.get_business_by_slug(business_slug)
    slots = service.get_available_slots(business.id, date, service_id, staff_id, branch_id)
    return PublicAvailableSlots(
        date=date,
        service_id=service_id,
        available_slots=slots
    )

@router.post("/book", response_model=PublicBookingResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    business_slug: str,
    data: PublicBookingCreate,
    service: PublicBookingService = Depends(get_service)
):
    return service.create_public_booking(business_slug, data)
