import uuid
from datetime import date
from typing import List, Optional
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.schedule_blocks.models import ScheduleBlock
from app.shared.enums.schedule_block import BlockType, RecurrenceDay

class ScheduleBlockRepository(BaseRepository[ScheduleBlock]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=ScheduleBlock)

    def list_by_business(self, business_id: uuid.UUID, page: int = 1, size: int = 20) -> List[ScheduleBlock]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
        ).order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())

    def get_by_business(self, business_id: uuid.UUID, block_id: uuid.UUID) -> Optional[ScheduleBlock]:
        statement = select(self.model).where(
            self.model.id == block_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
        )
        return self.db.scalars(statement).first()

    def list_active_blocks_for_date(self, business_id: uuid.UUID, target_date: date) -> List[ScheduleBlock]:
        # A bit of logic to match date or recurrence
        target_day_name = target_date.strftime("%A").upper()
        
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
            self.model.is_active.is_(True),
            or_(
                # FULL_DAY or TIME_RANGE where target_date is between start_date and end_date (or just equal to start_date)
                and_(
                    self.model.block_type.in_([BlockType.FULL_DAY, BlockType.TIME_RANGE]),
                    or_(
                        and_(self.model.start_date <= target_date, self.model.end_date >= target_date),
                        and_(self.model.start_date == target_date, self.model.end_date.is_(None))
                    )
                ),
                # RECURRING on the specific day
                and_(
                    self.model.block_type == BlockType.RECURRING,
                    self.model.recurrence_day == target_day_name
                )
            )
        )
        return list(self.db.scalars(statement).all())
