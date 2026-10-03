from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, time, datetime
from uuid import UUID
from app.shared.enums.schedule_block import BlockType, RecurrenceDay

class ScheduleBlockCreate(BaseModel):
    block_type: BlockType
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    recurrence_day: Optional[RecurrenceDay] = None
    reason: Optional[str] = None
    is_active: bool = True

class ScheduleBlockUpdate(BaseModel):
    block_type: Optional[BlockType] = None
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    recurrence_day: Optional[RecurrenceDay] = None
    reason: Optional[str] = None
    is_active: Optional[bool] = None

class ScheduleBlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    business_id: UUID
    block_type: BlockType
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    recurrence_day: Optional[RecurrenceDay] = None
    reason: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
