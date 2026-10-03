import uuid
from datetime import date, time
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, Text, ForeignKey, Date, Time, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.models.base import BaseModel
from app.shared.enums.schedule_block import BlockType, RecurrenceDay

class ScheduleBlock(BaseModel):
    __tablename__ = "schedule_blocks"

    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    # NULL = applies to the whole business, otherwise only to this branch
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=True, index=True
    )
    block_type: Mapped[BlockType] = mapped_column(
        SQLEnum(BlockType, name="blocktype", create_type=False), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    recurrence_day: Mapped[RecurrenceDay | None] = mapped_column(
        SQLEnum(RecurrenceDay, name="recurrenceday", create_type=False), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
