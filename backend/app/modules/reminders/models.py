import uuid
from datetime import datetime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.models.base import BaseModel
from app.shared.enums.reminder import ReminderChannel, ReminderStatus

class ReminderConfig(BaseModel):
    __tablename__ = "reminder_configs"

    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[ReminderChannel] = mapped_column(
        SQLEnum(ReminderChannel, name="reminderchannel", create_type=False), nullable=False
    )
    hours_before: Mapped[int] = mapped_column(Integer, nullable=False)
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ReminderLog(BaseModel):
    __tablename__ = "reminder_logs"

    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False
    )
    reminder_config_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("reminder_configs.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[ReminderChannel] = mapped_column(
        SQLEnum(ReminderChannel, name="reminderchannel", create_type=False), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[ReminderStatus] = mapped_column(
        SQLEnum(ReminderStatus, name="reminderstatus", create_type=False), nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
