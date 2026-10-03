from uuid import UUID
from datetime import date, time, timedelta
from typing import List, Optional
from fastapi import HTTPException
from app.db.unit_of_work import UnitOfWork
from app.core.exceptions import NotFoundException
from app.modules.business.repository import BusinessRepository
from app.modules.services.repository import ServiceRepository
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.models import Appointment
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.models import Customer
from app.shared.enums.appointment import AppointmentStatus
from app.modules.public_booking.schemas import PublicBookingCreate
from app.modules.schedule_blocks.repository import ScheduleBlockRepository
from app.modules.appointments.service import AppointmentService

class PublicBookingService:
    def __init__(
        self,
        business_repo: BusinessRepository,
        service_repo: ServiceRepository,
        appointment_repo: AppointmentRepository,
        customer_repo: CustomerRepository,
        appointment_service: AppointmentService,
        uow: UnitOfWork
    ):
        self.business_repo = business_repo
        self.service_repo = service_repo
        self.appointment_repo = appointment_repo
        self.customer_repo = customer_repo
        self.appointment_service = appointment_service
        self.uow = uow

    def get_business_by_slug(self, slug: str):
        business = self.business_repo.get_by_slug(slug)
        if not business:
            raise NotFoundException("Business not found")
        return business

    def list_public_services(self, business_id: UUID):
        return self.service_repo.list_active_by_business(business_id)

    def get_available_slots(self, business_id: UUID, target_date: date, service_id: UUID, staff_id: Optional[UUID] = None, branch_id: Optional[UUID] = None) -> List[time]:
        # get service duration
        service = self.service_repo.get_by_business(business_id, service_id)
        if not service:
            raise NotFoundException("Service not found")
            
        duration = service.duration_minutes or 30
        
        # AppointmentService.get_available_slots now handles schedule_blocks logic
        available_str = self.appointment_service.get_available_slots(business_id, target_date, duration_minutes=duration, staff_id=staff_id, branch_id=branch_id)
        
        # Convert string list back to time objects if needed, or just return them as strings depending on schema
        # PublicAvailableSlots schema expects time.
        # "09:00" -> time
        from datetime import datetime
        return [datetime.strptime(t_str, "%H:%M").time() for t_str in available_str]

    def create_public_booking(self, business_slug: str, data: PublicBookingCreate) -> Appointment:
        business = self.get_business_by_slug(business_slug)
        business_id = business.id
        
        service = self.service_repo.get_by_business(business_id, data.service_id)
        if not service:
            raise NotFoundException("Service not found")
            
        # Find or create customer
        customer = self.customer_repo.get_by_phone(business_id, data.customer_phone)
        if not customer:
            customer = Customer(
                business_id=business_id,
                name=data.customer_name,
                phone=data.customer_phone,
                email=data.customer_email
            )
            with self.uow:
                self.customer_repo.create(customer)
                self.uow.flush()
                self.uow.refresh(customer)
        
        from datetime import datetime
        start_datetime = datetime.combine(data.date, data.start_time)
        end_datetime = start_datetime + timedelta(minutes=service.duration_minutes or 30)
        
        appointment = Appointment(
            business_id=business_id,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            customer_email=data.customer_email,
            customer_id=customer.id,
            service_id=service.id,
            branch_id=data.branch_id,
            staff_id=data.staff_id,
            appointment_date=data.date,
            start_time=data.start_time,
            end_time=end_datetime.time(),
            status=AppointmentStatus.PENDING,
            notes="Booked via public booking page"
        )
        
        with self.uow:
            self.appointment_repo.create(appointment)
            self.uow.flush()
            self.uow.refresh(appointment)
            
        return appointment
