from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.staff.models import StaffProfile, StaffService, StaffSchedule
from app.modules.services.models import Service
from app.shared.enums.staff import StaffStatus

class StaffProfileRepository(BaseRepository[StaffProfile]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=StaffProfile)
        
    def list_by_business(self, business_id: UUID, branch_id: UUID | None = None, page: int = 1, size: int = 20) -> list[StaffProfile]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        if branch_id:
            query = query.where(self.model.branch_id == branch_id)
            
        query = query.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())
        
    def get_by_business(self, business_id: UUID, staff_id: UUID) -> StaffProfile | None:
        statement = select(self.model).where(
            self.model.id == staff_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalar(statement)
        
    def list_active(self, business_id: UUID, branch_id: UUID | None = None) -> list[StaffProfile]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.status == StaffStatus.ACTIVE,
            self.model.is_deleted.is_(False)
        )
        if branch_id:
            query = query.where(self.model.branch_id == branch_id)
        return list(self.db.scalars(query).all())

class StaffServiceRepository(BaseRepository[StaffService]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=StaffService)
        
    def list_services_for_staff(self, staff_id: UUID) -> list[Service]:
        statement = select(Service).join(
            self.model, self.model.service_id == Service.id
        ).where(
            self.model.staff_id == staff_id,
            self.model.is_deleted.is_(False),
            Service.is_deleted.is_(False)
        )
        return list(self.db.scalars(statement).all())
        
    def list_staff_for_service(self, service_id: UUID) -> list[StaffProfile]:
        statement = select(StaffProfile).join(
            self.model, self.model.staff_id == StaffProfile.id
        ).where(
            self.model.service_id == service_id,
            self.model.is_deleted.is_(False),
            StaffProfile.is_deleted.is_(False),
            StaffProfile.status == StaffStatus.ACTIVE
        )
        return list(self.db.scalars(statement).all())
        
    def remove_all_for_staff(self, staff_id: UUID) -> None:
        statement = delete(self.model).where(self.model.staff_id == staff_id)
        self.db.execute(statement)

class StaffScheduleRepository(BaseRepository[StaffSchedule]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=StaffSchedule)
        
    def get_schedule_for_staff(self, staff_id: UUID) -> list[StaffSchedule]:
        statement = select(self.model).where(
            self.model.staff_id == staff_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.day_of_week)
        return list(self.db.scalars(statement).all())
        
    def get_schedule_for_day(self, staff_id: UUID, day_of_week: int) -> StaffSchedule | None:
        statement = select(self.model).where(
            self.model.staff_id == staff_id,
            self.model.day_of_week == day_of_week,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalar(statement)
        
    def remove_all_for_staff(self, staff_id: UUID) -> None:
        statement = delete(self.model).where(self.model.staff_id == staff_id)
        self.db.execute(statement)
