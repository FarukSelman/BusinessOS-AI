import uuid
from datetime import date, time
from typing import List, Tuple, Optional
from app.db.unit_of_work import UnitOfWork
from app.core.exceptions import NotFoundException
from app.modules.schedule_blocks.repository import ScheduleBlockRepository
from app.modules.schedule_blocks.schemas import ScheduleBlockCreate, ScheduleBlockUpdate
from app.modules.schedule_blocks.models import ScheduleBlock
from app.shared.enums.schedule_block import BlockType

class ScheduleBlockService:
    def __init__(self, repository: ScheduleBlockRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    def create(self, business_id: uuid.UUID, data: ScheduleBlockCreate) -> ScheduleBlock:
        obj = ScheduleBlock(
            business_id=business_id,
            block_type=data.block_type,
            title=data.title,
            start_date=data.start_date,
            end_date=data.end_date,
            start_time=data.start_time,
            end_time=data.end_time,
            recurrence_day=data.recurrence_day,
            reason=data.reason,
            is_active=data.is_active
        )
        with self.uow:
            self.repository.create(obj)
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def list(self, business_id: uuid.UUID, page: int = 1, size: int = 20) -> List[ScheduleBlock]:
        return self.repository.list_by_business(business_id, page, size)

    def get(self, business_id: uuid.UUID, block_id: uuid.UUID) -> ScheduleBlock:
        obj = self.repository.get_by_business(business_id, block_id)
        if not obj:
            raise NotFoundException("Schedule block not found")
        return obj

    def update(self, business_id: uuid.UUID, block_id: uuid.UUID, data: ScheduleBlockUpdate) -> ScheduleBlock:
        obj = self.get(business_id, block_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(obj, field, value)
            
        with self.uow:
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def delete(self, business_id: uuid.UUID, block_id: uuid.UUID) -> None:
        obj = self.get(business_id, block_id)
        obj.is_deleted = True
        with self.uow:
            self.uow.flush()

    def get_blocked_times_for_date(self, business_id: uuid.UUID, target_date: date) -> List[Tuple[time, time]]:
        blocks = self.repository.list_active_blocks_for_date(business_id, target_date)
        
        blocked_times = []
        for block in blocks:
            if block.block_type == BlockType.FULL_DAY:
                blocked_times.append((time(0, 0), time(23, 59, 59)))
            elif block.block_type in (BlockType.TIME_RANGE, BlockType.RECURRING):
                # Using 00:00 to 23:59 as fallbacks if somehow time wasn't specified
                st = block.start_time or time(0, 0)
                et = block.end_time or time(23, 59, 59)
                blocked_times.append((st, et))
                
        return blocked_times
