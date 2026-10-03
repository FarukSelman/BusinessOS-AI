import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.reminders.models import ReminderConfig, ReminderLog

class ReminderConfigRepository(BaseRepository[ReminderConfig]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=ReminderConfig)

    def list_by_business(self, business_id: uuid.UUID, page: int = 1, size: int = 20) -> List[ReminderConfig]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
        ).order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())

    def get_by_business(self, business_id: uuid.UUID, config_id: uuid.UUID) -> Optional[ReminderConfig]:
        statement = select(self.model).where(
            self.model.id == config_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
        )
        return self.db.scalars(statement).first()

class ReminderLogRepository(BaseRepository[ReminderLog]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=ReminderLog)

    def list_by_business_and_appointment(
        self, business_id: uuid.UUID, appointment_id: Optional[uuid.UUID] = None, page: int = 1, size: int = 20
    ) -> List[ReminderLog]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
        )
        if appointment_id:
            query = query.where(self.model.appointment_id == appointment_id)
            
        statement = query.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())
