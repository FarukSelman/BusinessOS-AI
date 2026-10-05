import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class InsightStatus:
    GENERATING = "GENERATING"
    READY = "READY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    FAILED = "FAILED"


class InsightTrigger:
    NIGHTLY = "NIGHTLY"
    FIRST_VIEW = "FIRST_VIEW"
    MANUAL = "MANUAL"


class BusinessInsight(BaseModel):
    """
    One generation attempt of the dashboard "AI İçgörüleri" card.

    Rows are kept as history; the dashboard shows the newest READY or
    INSUFFICIENT_DATA row, so a failed attempt never hides a good insight.
    `metrics` holds only aggregated numbers (see metrics.py) - never
    customer or staff personal data.
    """

    __tablename__ = "business_insights"
    __table_args__ = (Index("ix_business_insights_business_created", "business_id", "created_at"),)

    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    trigger: Mapped[str] = mapped_column(String(20), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    items: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    model: Mapped[str | None] = mapped_column(String(60), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
