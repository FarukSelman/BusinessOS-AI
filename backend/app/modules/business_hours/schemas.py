from datetime import date, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BusinessHoursItem(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    is_closed: bool = False

    @model_validator(mode="after")
    def check_times(self):
        if self.is_closed:
            self.open_time = None
            self.close_time = None
            return self
        if self.open_time is None or self.close_time is None:
            raise ValueError("open_time and close_time are required when the day is not closed.")
        if self.open_time >= self.close_time:
            raise ValueError("open_time must be earlier than close_time.")
        return self


class BusinessHoursSet(BaseModel):
    items: list[BusinessHoursItem] = Field(..., max_length=7)

    @field_validator("items")
    @classmethod
    def unique_days(cls, items: list[BusinessHoursItem]) -> list[BusinessHoursItem]:
        days = [item.day_of_week for item in items]
        if len(days) != len(set(days)):
            raise ValueError("Each day_of_week may appear only once.")
        return items


class BusinessHoursResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_id: UUID
    branch_id: Optional[UUID] = None
    day_of_week: int
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    is_closed: bool


class OpenWindowResponse(BaseModel):
    date: date
    branch_id: Optional[UUID] = None
    is_open: bool
    open_time: Optional[time] = None
    close_time: Optional[time] = None
