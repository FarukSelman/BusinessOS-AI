import uuid
from datetime import time

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, Time, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class BusinessHours(BaseModel):
    """
    Weekly opening hours.

    branch_id NULL  -> business-wide hours (default for every branch)
    branch_id set   -> branch-specific hours, overrides the business-wide week
    """

    __tablename__ = "business_hours"

    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("branches.id", ondelete="CASCADE"), nullable=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    open_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    close_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_business_hours_day_of_week"),
        CheckConstraint(
            "is_closed OR (open_time IS NOT NULL AND close_time IS NOT NULL AND open_time < close_time)",
            name="ck_business_hours_open_before_close",
        ),
        # One row per day per scope. Two partial indexes because NULLs are never equal in a unique index.
        Index(
            "uq_business_hours_business_day", "business_id", "day_of_week",
            unique=True, postgresql_where=text("branch_id IS NULL"),
        ),
        Index(
            "uq_business_hours_branch_day", "branch_id", "day_of_week",
            unique=True, postgresql_where=text("branch_id IS NOT NULL"),
        ),
    )
