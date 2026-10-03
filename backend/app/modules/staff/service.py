from datetime import date, time
from uuid import UUID
from app.core.exceptions import NotFoundException
from app.db.unit_of_work import UnitOfWork
from app.modules.staff.models import StaffProfile, StaffService, StaffSchedule
from app.modules.staff.repository import StaffProfileRepository, StaffServiceRepository, StaffScheduleRepository
from app.modules.staff.schemas import StaffCreate, StaffUpdate, StaffScheduleSet, StaffResponse
from app.modules.services.models import Service

class StaffServiceDomain:
    def __init__(
        self, 
        profile_repo: StaffProfileRepository, 
        service_repo: StaffServiceRepository,
        schedule_repo: StaffScheduleRepository,
        uow: UnitOfWork
    ):
        self.profile_repo = profile_repo
        self.service_repo = service_repo
        self.schedule_repo = schedule_repo
        self.uow = uow
        
    def _enrich_staff(self, staff: StaffProfile) -> dict:
        staff_data = staff.__dict__.copy()
        staff_data["services"] = self.service_repo.list_services_for_staff(staff.id)
        return staff_data

    def list_staff(self, business_id: UUID, branch_id: UUID | None = None, page: int = 1, size: int = 20) -> list[dict]:
        staff_list = self.profile_repo.list_by_business(business_id=business_id, branch_id=branch_id, page=page, size=size)
        return [self._enrich_staff(s) for s in staff_list]
        
    def get_staff(self, business_id: UUID, staff_id: UUID) -> dict:
        staff = self.profile_repo.get_by_business(business_id=business_id, staff_id=staff_id)
        if not staff:
            raise NotFoundException("Staff profile not found")
        return self._enrich_staff(staff)
        
    def create_staff(self, business_id: UUID, data: StaffCreate) -> dict:
        staff_data = data.model_dump()
        
        with self.uow:
            staff = StaffProfile(business_id=business_id, **staff_data)
            self.profile_repo.create(staff)
            self.uow.flush()
            self.uow.refresh(staff)
            return self._enrich_staff(staff)
            
    def update_staff(self, business_id: UUID, staff_id: UUID, data: StaffUpdate) -> dict:
        staff = self.profile_repo.get_by_business(business_id=business_id, staff_id=staff_id)
        if not staff:
            raise NotFoundException("Staff profile not found")
            
        update_data = data.model_dump(exclude_unset=True)
        
        with self.uow:
            for key, value in update_data.items():
                setattr(staff, key, value)
            self.uow.flush()
            self.uow.refresh(staff)
            return self._enrich_staff(staff)
            
    def delete_staff(self, business_id: UUID, staff_id: UUID) -> None:
        staff = self.profile_repo.get_by_business(business_id=business_id, staff_id=staff_id)
        if not staff:
            raise NotFoundException("Staff profile not found")
            
        with self.uow:
            self.profile_repo.soft_delete(staff)
            self.uow.flush()

    def assign_services(self, business_id: UUID, staff_id: UUID, service_ids: list[UUID]) -> dict:
        staff = self.profile_repo.get_by_business(business_id=business_id, staff_id=staff_id)
        if not staff:
            raise NotFoundException("Staff profile not found")
            
        with self.uow:
            self.service_repo.remove_all_for_staff(staff_id)
            for sid in service_ids:
                link = StaffService(staff_id=staff_id, service_id=sid)
                self.service_repo.create(link)
            self.uow.flush()
            return self._enrich_staff(staff)
            
    def list_staff_services(self, staff_id: UUID) -> list[Service]:
        return self.service_repo.list_services_for_staff(staff_id)
        
    def set_schedule(self, business_id: UUID, staff_id: UUID, data: StaffScheduleSet) -> list[StaffSchedule]:
        staff = self.profile_repo.get_by_business(business_id=business_id, staff_id=staff_id)
        if not staff:
            raise NotFoundException("Staff profile not found")
            
        with self.uow:
            self.schedule_repo.remove_all_for_staff(staff_id)
            
            schedules = []
            for item in data.items:
                schedule = StaffSchedule(
                    staff_id=staff_id,
                    business_id=business_id,
                    day_of_week=item.day_of_week,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    is_working=item.is_working
                )
                self.schedule_repo.create(schedule)
                schedules.append(schedule)
                
            self.uow.flush()
            return schedules
            
    def get_schedule(self, staff_id: UUID) -> list[StaffSchedule]:
        return self.schedule_repo.get_schedule_for_staff(staff_id)
        
    def get_available_staff_for_slot(
        self, 
        business_id: UUID, 
        date_obj: date, 
        start_time: time, 
        service_id: UUID, 
        branch_id: UUID | None = None
    ) -> list[StaffProfile]:
        # For simplicity in this phase, we just return staff who provide this service
        # and optionally work at this branch.
        # More advanced: check staff schedules, existing appointments.
        staff_for_service = self.service_repo.list_staff_for_service(service_id)
        
        # Filter by branch if provided
        if branch_id:
            staff_for_service = [s for s in staff_for_service if s.branch_id == branch_id or s.branch_id is None]
            
        return staff_for_service
