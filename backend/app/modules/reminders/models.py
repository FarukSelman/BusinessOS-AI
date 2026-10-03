import uuid
from datetime import datetime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, Text, ForeignKey, DateTime, Boolean, UniqueConstraint, Index
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
    """
    One row per (appointment, reminder config, appointment start time).

    The unique constraint is what guarantees a reminder is sent at most once:
    the sender first claims the row with INSERT ... ON CONFLICT DO NOTHING and
    only the process that inserted it sends the e-mail. Including the start
    time means a rescheduled appointment gets a fresh reminder.
    """
    __tablename__ = "reminder_logs"
    __table_args__ = (
        UniqueConstraint(
            "appointment_id", "reminder_config_id", "appointment_start",
            name="uq_reminder_logs_appointment_config_start",
        ),
        Index("ix_reminder_logs_business_created", "business_id", "created_at"),
    )

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
    # Appointment start (local time, APP_TIMEZONE) this reminder was for.
    appointment_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    recipient_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Local time (APP_TIMEZONE), same convention as appointment dates/times.
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[ReminderStatus] = mapped_column(
        SQLEnum(ReminderStatus, name="reminderstatus", create_type=False), nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
