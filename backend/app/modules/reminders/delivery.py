"""
Appointment reminder delivery.

send_due_reminders() is called every REMINDER_SCAN_INTERVAL_SECONDS by Celery
beat (app/workers). It is a plain function so it can be run and tested
without Celery.

Rules
- Only active EMAIL configs of active, non-deleted businesses. No config ->
  nothing is sent (reminders are opt-in per business).
- Only PENDING / CONFIRMED, non-deleted appointments whose start is at least
  REMINDER_MIN_LEAD_MINUTES away.
- A config is due when  start - hours_before <= now.  If several configs are
  due at once (late booking), only the closest one (smallest hours_before) is
  sent; the others are logged as SKIPPED. A config is also skipped when
  another reminder for the same appointment was already sent inside its
  window, so a customer never gets two reminders back to back.
- At most once: a reminder_logs row is claimed with INSERT ... ON CONFLICT DO
  NOTHING on (appointment_id, reminder_config_id, appointment_start) and
  committed BEFORE the e-mail is sent; only the claimer sends. A rescheduled
  appointment has a new start, so it gets a new reminder.
- Failures are retried on later scans up to REMINDER_MAX_ATTEMPTS.

All times are naive local times in APP_TIMEZONE, the same convention as
appointment_date / start_time.
"""
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.appointments.models import Appointment
from app.modules.branches.models import Branch
from app.modules.business.models import Business
from app.modules.customers.models import Customer
from app.modules.reminders.models import ReminderConfig, ReminderLog
from app.modules.reminders.templating import build_reminder_email, format_date_tr, format_time
from app.modules.services.models import Service
from app.modules.staff.models import StaffProfile
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.business import BusinessStatus
from app.shared.enums.reminder import ReminderChannel, ReminderStatus
from app.shared.mail.smtp import SMTPClient

logger = logging.getLogger(__name__)

REMINDABLE_STATUSES = (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LOGS = ReminderLog.__table__
CONSTRAINT = "uq_reminder_logs_appointment_config_start"

SKIP_SUPERSEDED = "Daha yakın zamanlı bir hatırlatma gönderildiği için atlandı."
SKIP_NO_EMAIL = "Müşterinin geçerli bir e-posta adresi yok."


@dataclass
class DeliveryReport:
    sent: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"sent": self.sent, "failed": self.failed, "skipped": self.skipped, "errors": self.errors[:10]}


class SMTPMailer:
    """Sends a batch over one SMTP connection, reconnecting after an error."""

    def __init__(self):
        self._context = None
        self._server = None

    def send(self, to_email: str, subject: str, html: str, text: str) -> None:
        message = SMTPClient.build_message(to_email, subject, html, text)
        try:
            if self._server is None:
                self._context = SMTPClient.connection()
                self._server = self._context.__enter__()
            self._server.send_message(message)
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if self._context is not None:
            try:
                self._context.__exit__(None, None, None)
            except Exception:  # pragma: no cover - best effort
                pass
        self._context = self._server = None


def local_now(now: datetime | None = None) -> datetime:
    """Current time as a naive datetime in APP_TIMEZONE."""
    tz = ZoneInfo(settings.APP_TIMEZONE)
    if now is None:
        now = datetime.now(tz)
    if now.tzinfo is not None:
        now = now.astimezone(tz).replace(tzinfo=None)
    return now


def send_due_reminders(db: Session, now: datetime | None = None, mailer=None) -> DeliveryReport:
    now = local_now(now)
    report = DeliveryReport()
    own_mailer = mailer is None
    mailer = mailer or SMTPMailer()
    try:
        configs = (
            db.query(ReminderConfig)
            .join(Business, Business.id == ReminderConfig.business_id)
            .filter(
                ReminderConfig.is_active.is_(True),
                ReminderConfig.is_deleted.is_(False),
                ReminderConfig.channel == ReminderChannel.EMAIL,
                ReminderConfig.hours_before > 0,
                Business.is_deleted.is_(False),
                Business.status == BusinessStatus.ACTIVE,
            )
            .all()
        )
        by_business: dict[uuid.UUID, list[ReminderConfig]] = {}
        for config in configs:
            by_business.setdefault(config.business_id, []).append(config)

        for business_id, business_configs in by_business.items():
            try:
                _process_business(db, business_id, business_configs, now, mailer, report)
            except Exception as exc:  # one broken business must not stop the others
                db.rollback()
                logger.exception("Reminder scan failed for business %s", business_id)
                report.errors.append(f"{business_id}: {exc}")
    finally:
        if own_mailer:
            mailer.close()
    logger.info("Reminder scan at %s: %s", now, report.as_dict())
    return report


def _process_business(db, business_id, configs, now, mailer, report) -> None:
    configs = sorted(configs, key=lambda c: c.hours_before)
    max_hours = configs[-1].hours_before
    earliest_start = now + timedelta(minutes=settings.REMINDER_MIN_LEAD_MINUTES)
    latest_start = now + timedelta(hours=max_hours)

    appointments = [
        a for a in db.query(Appointment).filter(
            Appointment.business_id == business_id,
            Appointment.is_deleted.is_(False),
            Appointment.status.in_(REMINDABLE_STATUSES),
            Appointment.appointment_date >= earliest_start.date(),
            Appointment.appointment_date <= latest_start.date(),
        ).all()
        if earliest_start <= datetime.combine(a.appointment_date, a.start_time) <= latest_start
    ]
    if not appointments:
        return

    logs: dict[tuple, dict] = {}
    for log in db.query(ReminderLog).filter(
        ReminderLog.appointment_id.in_([a.id for a in appointments]),
        ReminderLog.is_deleted.is_(False),
    ).all():
        logs.setdefault((log.appointment_id, log.appointment_start), {})[log.reminder_config_id] = log

    lookups = _Lookups(db, business_id)

    for appt in appointments:
        start = datetime.combine(appt.appointment_date, appt.start_time)
        existing = logs.get((appt.id, start), {})
        due = [c for c in configs if start - timedelta(hours=c.hours_before) <= now]
        open_configs = [c for c in due if c.id not in existing or _retryable(existing[c.id])]
        if not open_configs:
            continue

        chosen, others = open_configs[0], open_configs[1:]
        for other in others:
            if other.id not in existing and _claim(db, appt, other, start, ReminderStatus.SKIPPED, error=SKIP_SUPERSEDED):
                report.skipped += 1

        last_sent = max((l.sent_at for l in existing.values() if l.status == ReminderStatus.SENT and l.sent_at), default=None)
        if last_sent and last_sent >= start - timedelta(hours=chosen.hours_before):
            if chosen.id not in existing and _claim(db, appt, chosen, start, ReminderStatus.SKIPPED, error=SKIP_SUPERSEDED):
                report.skipped += 1
            continue

        recipient = (appt.customer_email or lookups.customer_email(appt.customer_id) or "").strip()
        if not EMAIL_RE.match(recipient):
            if chosen.id not in existing and _claim(db, appt, chosen, start, ReminderStatus.SKIPPED, error=SKIP_NO_EMAIL):
                report.skipped += 1
            continue

        log_id = (
            _claim_retry(db, existing[chosen.id]) if chosen.id in existing
            else _claim(db, appt, chosen, start, ReminderStatus.PENDING, recipient=recipient)
        )
        if log_id is None:
            continue  # another worker claimed it first

        subject, html, text = build_reminder_email(chosen.message_template, lookups.context(appt, start))
        try:
            mailer.send(recipient, subject, html, text)
        except Exception as exc:
            _finish(db, log_id, ReminderStatus.FAILED, error=f"{type(exc).__name__}: {exc}")
            report.failed += 1
            report.errors.append(f"{appt.id}: {exc}")
        else:
            _finish(db, log_id, ReminderStatus.SENT, sent_at=local_now())
            report.sent += 1


def _retryable(log: ReminderLog) -> bool:
    return log.status == ReminderStatus.FAILED and log.attempts < settings.REMINDER_MAX_ATTEMPTS


def _claim(db, appt, config, start, status, *, error=None, recipient=None):
    """Inserts the log row; returns its id, or None if it already existed."""
    stamp = datetime.now(UTC)
    stmt = (
        pg_insert(LOGS)
        .values(
            id=uuid.uuid4(), created_at=stamp, updated_at=stamp, is_deleted=False,
            business_id=appt.business_id, appointment_id=appt.id, reminder_config_id=config.id,
            channel=ReminderChannel.EMAIL, appointment_start=start, status=status,
            attempts=1 if status == ReminderStatus.PENDING else 0,
            recipient_email=recipient, error_message=error,
        )
        .on_conflict_do_nothing(constraint=CONSTRAINT)
        .returning(LOGS.c.id)
    )
    log_id = db.execute(stmt).scalar()
    db.commit()  # make the claim visible to other workers before sending
    return log_id


def _claim_retry(db, log: ReminderLog):
    stmt = (
        update(LOGS)
        .where(
            LOGS.c.id == log.id,
            LOGS.c.status == ReminderStatus.FAILED,
            LOGS.c.attempts < settings.REMINDER_MAX_ATTEMPTS,
        )
        .values(status=ReminderStatus.PENDING, attempts=LOGS.c.attempts + 1, updated_at=datetime.now(UTC))
        .returning(LOGS.c.id)
    )
    log_id = db.execute(stmt).scalar()
    db.commit()
    return log_id


def _finish(db, log_id, status, *, error=None, sent_at=None) -> None:
    db.execute(
        update(LOGS)
        .where(LOGS.c.id == log_id)
        .values(status=status, error_message=(error or None) and error[:1000], sent_at=sent_at, updated_at=datetime.now(UTC))
    )
    db.commit()


class _Lookups:
    """Names for the template, fetched once per business."""

    def __init__(self, db, business_id):
        self.db = db
        self.business = db.get(Business, business_id)
        self._services: dict = {}
        self._staff: dict = {}
        self._branches: dict = {}
        self._customers: dict = {}

    def _get(self, cache, model, key):
        if key is None:
            return None
        if key not in cache:
            cache[key] = self.db.get(model, key)
        return cache[key]

    def customer_email(self, customer_id):
        customer = self._get(self._customers, Customer, customer_id)
        return customer.email if customer and customer.business_id == self.business.id else None

    def context(self, appt: Appointment, start: datetime) -> dict:
        service = self._get(self._services, Service, appt.service_id)
        staff = self._get(self._staff, StaffProfile, appt.staff_id)
        branch = self._get(self._branches, Branch, appt.branch_id)
        return {
            "customer_name": appt.customer_name,
            "appointment_date": format_date_tr(start.date()),
            "start_time": format_time(start.time()),
            "service_name": service.name if service else None,
            "staff_name": staff.full_name if staff else None,
            "business_name": self.business.name,
            "branch_name": branch.name if branch else None,
            "branch_address": branch.address if branch else None,
        }
