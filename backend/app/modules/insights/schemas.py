from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


class InsightItem(BaseModel):
    type: Literal["positive", "negative", "neutral", "suggestion"]
    title: str
    detail: str
    metric: str
    badge: Optional[str] = None


class InsightProgress(BaseModel):
    appointments: int
    required: int


class InsightResponse(BaseModel):
    """What the dashboard card needs; never contains raw metrics or personal data."""

    state: Literal["ready", "insufficient_data", "generating", "unavailable", "not_configured"]
    summary: Optional[str] = None
    items: list[InsightItem] = []
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    generated_at: Optional[datetime] = None
    stale: bool = False                 # shown insight is from an earlier day
    last_attempt_failed: bool = False   # newest attempt failed; older insight shown
    generating: bool = False
    can_refresh: bool = False
    next_refresh_at: Optional[datetime] = None
    progress: Optional[InsightProgress] = None
