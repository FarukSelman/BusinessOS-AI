"""
Generation, storage and read model of the "AI İçgörüleri" card.

When insights are produced
- NIGHTLY: Celery beat at 03:00 (APP_TIMEZONE) for every active business.
- FIRST_VIEW: the first dashboard visit of a day without today's insight
  starts one background generation (new businesses do not wait for night).
- MANUAL: "Yenile" button, owner/admin only, once per hour per business.

Robustness
- The dashboard only ever reads stored rows; it never waits for OpenAI.
- Every attempt is a row. Failures are recorded as FAILED and never replace
  the last good insight. A GENERATING row older than STALE_AFTER counts as
  failed (e.g. the server restarted mid-generation).
- Not enough data -> INSUFFICIENT_DATA without calling the model.
"""
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.modules.insights import generator
from app.modules.insights.metrics import MIN_APPOINTMENTS_60D, build_metrics, has_enough_data, periods
from app.modules.insights.models import BusinessInsight, InsightStatus, InsightTrigger

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(minutes=3)        # GENERATING older than this = crashed
FIRST_VIEW_RETRY_AFTER = timedelta(minutes=10)  # do not hammer OpenAI after a failure

# Patched in tests: background generation opens its own session.
SESSION_FACTORY = SessionLocal


def local_today() -> date:
    return datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date()


def local_date(moment: datetime | None) -> date | None:
    return moment.astimezone(ZoneInfo(settings.APP_TIMEZONE)).date() if moment else None


def get_insights_client():
    """OpenAI client, or None when no API key is configured. Patched in tests."""
    if not settings.OPENAI_API_KEY:
        return None
    from app.ai.openai.client import OpenAIClient

    return OpenAIClient()


def is_configured() -> bool:
    return bool(settings.OPENAI_API_KEY)


@dataclass
class InsightState:
    state: str  # ready | insufficient_data | generating | unavailable | not_configured
    shown: BusinessInsight | None
    generating: bool
    last_attempt_failed: bool
    can_refresh: bool
    next_refresh_at: datetime | None


class InsightService:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ reads

    def _rows(self, business_id: UUID, *statuses: str, trigger: str | None = None) -> select:
        q = select(BusinessInsight).where(
            BusinessInsight.business_id == business_id, BusinessInsight.is_deleted.is_(False)
        )
        if statuses:
            q = q.where(BusinessInsight.status.in_(statuses))
        if trigger:
            q = q.where(BusinessInsight.trigger == trigger)
        return q.order_by(BusinessInsight.created_at.desc()).limit(1)

    def latest_shown(self, business_id: UUID) -> BusinessInsight | None:
        return self.db.scalar(self._rows(business_id, InsightStatus.READY, InsightStatus.INSUFFICIENT_DATA))

    def latest_attempt(self, business_id: UUID) -> BusinessInsight | None:
        return self.db.scalar(self._rows(business_id))

    def running(self, business_id: UUID, now: datetime) -> BusinessInsight | None:
        row = self.db.scalar(self._rows(business_id, InsightStatus.GENERATING))
        return row if row and now - row.created_at < STALE_AFTER else None

    def next_manual_refresh(self, business_id: UUID) -> datetime | None:
        last = self.db.scalar(self._rows(business_id, trigger=InsightTrigger.MANUAL))
        if last is None:
            return None
        allowed = last.created_at + timedelta(minutes=settings.INSIGHTS_REFRESH_COOLDOWN_MINUTES)
        return allowed if allowed > datetime.now(UTC) else None

    def state(self, business_id: UUID) -> InsightState:
        now = datetime.now(UTC)
        shown = self.latest_shown(business_id)
        attempt = self.latest_attempt(business_id)
        generating = self.running(business_id, now) is not None
        failed_after_shown = bool(
            attempt and attempt.status in (InsightStatus.FAILED, InsightStatus.GENERATING) and not generating
            and (shown is None or attempt.created_at > shown.created_at)
        )
        next_refresh = self.next_manual_refresh(business_id)

        if generating:
            state = "generating"
        elif shown is not None:
            state = "ready" if shown.status == InsightStatus.READY else "insufficient_data"
        elif not is_configured():
            state = "not_configured"
        else:
            state = "unavailable"
        return InsightState(
            state=state,
            shown=shown,
            generating=generating,
            last_attempt_failed=failed_after_shown,
            can_refresh=is_configured() and not generating and next_refresh is None,
            next_refresh_at=next_refresh,
        )

    def needs_first_view_generation(self, business_id: UUID) -> bool:
        if not is_configured():
            return False
        now = datetime.now(UTC)
        if self.running(business_id, now):
            return False
        shown = self.latest_shown(business_id)
        if shown is not None and local_date(shown.generated_at) == local_today():
            return False
        attempt = self.latest_attempt(business_id)
        return not (attempt and now - attempt.created_at < FIRST_VIEW_RETRY_AFTER)

    # ------------------------------------------------------------------ writes

    def start(self, business_id: UUID, trigger: str, user_id: UUID | None = None) -> BusinessInsight | None:
        """Creates the GENERATING row, or returns None when one is already running."""
        self.db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": f"insights:{business_id}"},
        )
        if self.running(business_id, datetime.now(UTC)):
            self.db.rollback()
            return None
        current, _ = periods(local_today())
        row = BusinessInsight(
            business_id=business_id, status=InsightStatus.GENERATING, trigger=trigger,
            period_start=current.start, period_end=current.end, requested_by=user_id,
        )
        self.db.add(row)
        self.db.commit()  # releases the lock
        return row

    def complete(self, row: BusinessInsight, client=None) -> BusinessInsight:
        """Fills a GENERATING row. Never raises: problems end as FAILED."""
        today = local_today()
        try:
            enough, appointments_60d, revenue_60d = has_enough_data(self.db, row.business_id, today)
            if not enough:
                row.status = InsightStatus.INSUFFICIENT_DATA
                row.metrics = {"appointments_60d": appointments_60d, "revenue_60d": revenue_60d,
                               "required_appointments": MIN_APPOINTMENTS_60D}
            else:
                metrics = build_metrics(self.db, row.business_id, today)
                row.metrics = metrics
                client = client or get_insights_client()
                if client is None:
                    raise RuntimeError("OPENAI_API_KEY tanımlı değil.")
                result = generator.generate(client, metrics, settings.INSIGHTS_MODEL, settings.INSIGHTS_TIMEOUT_SECONDS)
                row.status = InsightStatus.READY
                row.summary, row.items, row.model = result.summary, result.items, settings.INSIGHTS_MODEL
            row.generated_at = datetime.now(UTC)
            row.error = None
        except Exception as exc:
            self.db.rollback()
            row = self.db.get(BusinessInsight, row.id) or row
            row.status = InsightStatus.FAILED
            row.error = f"{type(exc).__name__}: {exc}"[:1000]
            logger.warning("Insight generation failed for business %s: %s", row.business_id, row.error)
        self.db.commit()
        return row

    def generate_now(self, business_id: UUID, trigger: str, user_id: UUID | None = None, client=None):
        row = self.start(business_id, trigger, user_id)
        return self.complete(row, client) if row else None


def run_generation(insight_id: UUID) -> None:
    """Background task (FastAPI): its own DB session, never raises."""
    db = SESSION_FACTORY()
    try:
        row = db.get(BusinessInsight, insight_id)
        if row is not None and row.status == InsightStatus.GENERATING:
            InsightService(db).complete(row)
    except Exception:
        logger.exception("Insight background generation crashed")
    finally:
        db.close()


def generate_for_all_businesses(db: Session) -> dict:
    """Nightly Celery job."""
    from app.modules.business.models import Business
    from app.shared.enums.business import BusinessStatus

    report = {"ready": 0, "insufficient_data": 0, "failed": 0, "skipped": 0}
    if not is_configured():
        report["skipped"] = -1  # not configured: nothing to do
        return report
    business_ids = db.scalars(
        select(Business.id).where(Business.is_deleted.is_(False), Business.status == BusinessStatus.ACTIVE)
    ).all()
    service = InsightService(db)
    for business_id in business_ids:
        row = service.generate_now(business_id, InsightTrigger.NIGHTLY)
        if row is None:
            report["skipped"] += 1
        elif row.status == InsightStatus.READY:
            report["ready"] += 1
        elif row.status == InsightStatus.INSUFFICIENT_DATA:
            report["insufficient_data"] += 1
        else:
            report["failed"] += 1
    return report
