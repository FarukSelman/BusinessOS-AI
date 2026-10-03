"""
Appointment reminder e-mails.

- Unit tests (no database): templating, SMTP client settings, Celery wiring.
- Integration tests (PostgreSQL, skipped when unreachable): send_due_reminders
  rules, duplicate prevention, retries, and the reminders API.

No real e-mail is sent: a FakeMailer collects messages and smtplib is mocked.
"""
import smtplib
import threading
import uuid
from datetime import date, datetime, time, timedelta
from unittest import mock

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.modules.appointments.models import Appointment
from app.modules.branches.models import Branch
from app.modules.business.models import Business
from app.modules.customers.models import Customer
from app.modules.membership.models import Membership
from app.modules.reminders import delivery
from app.modules.reminders.delivery import SKIP_NO_EMAIL, SKIP_SUPERSEDED, local_now, send_due_reminders
from app.modules.reminders.models import ReminderConfig, ReminderLog
from app.modules.reminders.schemas import ReminderConfigCreate, ReminderConfigUpdate
from app.modules.reminders.templating import build_reminder_email, format_date_tr, render
from app.modules.services.models import Service
from app.modules.staff.models import StaffProfile
from app.modules.user.models import User
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.business import BusinessStatus
from app.shared.enums.membership import MembershipRole
from app.shared.enums.reminder import ReminderChannel, ReminderStatus
from app.shared.enums.user import UserStatus
from app.shared.mail.smtp import SMTPClient
from tests.pg_support import API, auth, make_client, make_engine, release_client

NOW = datetime(2026, 10, 5, 10, 0)  # Monday 10:00 local time


# ====================================================================== unit: templating

def test_format_date_is_turkish():
    assert format_date_tr(date(2026, 10, 6)) == "6 Ekim 2026 Salı"
    assert format_date_tr(date(2026, 2, 1)) == "1 Şubat 2026 Pazar"


def test_render_fills_known_and_keeps_unknown_placeholders():
    out = render("Merhaba {{customer_name}}, {{ start_time }} {{unknown}}", {"customer_name": "Ali", "start_time": "14:00"}, escape=False)
    assert out == "Merhaba Ali, 14:00 {{unknown}}"


def test_render_missing_value_becomes_empty():
    assert render("[{{service_name}}]", {"service_name": None}, escape=False) == "[]"


def test_html_body_escapes_customer_data_but_text_does_not():
    subject, html, text = build_reminder_email(
        "Sayın {{customer_name}}", {"customer_name": "<b>Ali</b> & Co", "business_name": "Kuaför"}
    )
    assert subject == "Randevu hatırlatması – Kuaför"
    assert "&lt;b&gt;Ali&lt;/b&gt; &amp; Co" in html
    assert "<b>Ali</b>" not in html
    assert text.startswith("Sayın <b>Ali</b> & Co")


def test_email_lists_only_present_details():
    _, html, text = build_reminder_email(
        "x", {"appointment_date": "6 Ekim 2026 Salı", "start_time": "14:30", "service_name": "Saç Kesimi",
              "staff_name": None, "branch_name": None, "business_name": "B"},
    )
    assert "Saç Kesimi" in html and "Hizmet: Saç Kesimi" in text
    assert "Personel" not in text and "Şube" not in text


# ====================================================================== unit: schemas

def test_sms_channel_is_rejected():
    with pytest.raises(ValidationError):
        ReminderConfigCreate(channel=ReminderChannel.SMS, hours_before=24, message_template="x")
    with pytest.raises(ValidationError):
        ReminderConfigUpdate(channel=ReminderChannel.SMS)


@pytest.mark.parametrize("hours", [0, -1, 169])
def test_hours_before_bounds(hours):
    with pytest.raises(ValidationError):
        ReminderConfigCreate(channel=ReminderChannel.EMAIL, hours_before=hours, message_template="x")


def test_template_cannot_be_blank_or_too_long():
    with pytest.raises(ValidationError):
        ReminderConfigCreate(channel=ReminderChannel.EMAIL, hours_before=24, message_template="   ")
    with pytest.raises(ValidationError):
        ReminderConfigCreate(channel=ReminderChannel.EMAIL, hours_before=24, message_template="x" * 2001)


# ====================================================================== unit: SMTP client

@pytest.fixture
def mail_settings(monkeypatch):
    def apply(**values):
        base = dict(MAIL_SERVER="smtp.test", MAIL_PORT=2525, MAIL_USERNAME="user", MAIL_PASSWORD="pw",
                    MAIL_FROM="no-reply@businessos.test", MAIL_FROM_NAME="BusinessOS", MAIL_USE_TLS=True,
                    MAIL_USE_SSL=False, MAIL_TIMEOUT_SECONDS=7)
        base.update(values)
        for key, value in base.items():
            monkeypatch.setattr(settings, key, value)
    apply()
    return apply


def test_smtp_starttls_login_and_timeout(mail_settings):
    with mock.patch("app.shared.mail.smtp.smtplib.SMTP") as smtp_cls:
        SMTPClient.send("a@b.co", "Konu", "<p>hi</p>", "hi")
    smtp_cls.assert_called_once_with("smtp.test", 2525, timeout=7)
    server = smtp_cls.return_value
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("user", "pw")
    message = server.send_message.call_args.args[0]
    assert message["To"] == "a@b.co"
    assert message["From"] == "BusinessOS <no-reply@businessos.test>"
    assert message.is_multipart() and len(message.get_payload()) == 2  # text + html
    server.quit.assert_called_once()


def test_smtp_ssl_mode_uses_smtp_ssl_without_starttls(mail_settings):
    mail_settings(MAIL_USE_SSL=True, MAIL_PORT=465)
    with mock.patch("app.shared.mail.smtp.smtplib.SMTP_SSL") as ssl_cls, mock.patch("app.shared.mail.smtp.smtplib.SMTP") as plain:
        SMTPClient.send("a@b.co", "s", "<p>x</p>")
    ssl_cls.assert_called_once_with("smtp.test", 465, timeout=7)
    ssl_cls.return_value.starttls.assert_not_called()
    plain.assert_not_called()


def test_smtp_without_username_skips_login(mail_settings):
    mail_settings(MAIL_USERNAME="", MAIL_USE_TLS=False)
    with mock.patch("app.shared.mail.smtp.smtplib.SMTP") as smtp_cls:
        SMTPClient.send("a@b.co", "s", "<p>x</p>")
    smtp_cls.return_value.login.assert_not_called()
    smtp_cls.return_value.starttls.assert_not_called()


def test_smtp_closes_connection_when_send_fails(mail_settings):
    with mock.patch("app.shared.mail.smtp.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.send_message.side_effect = smtplib.SMTPRecipientsRefused({})
        with pytest.raises(smtplib.SMTPRecipientsRefused):
            SMTPClient.send("a@b.co", "s", "<p>x</p>")
    smtp_cls.return_value.quit.assert_called_once()


def test_batch_mailer_reuses_one_connection(mail_settings):
    with mock.patch("app.shared.mail.smtp.smtplib.SMTP") as smtp_cls:
        mailer = delivery.SMTPMailer()
        mailer.send("a@b.co", "s", "h", "t")
        mailer.send("c@d.co", "s", "h", "t")
        mailer.close()
    assert smtp_cls.call_count == 1
    assert smtp_cls.return_value.send_message.call_count == 2


# ====================================================================== unit: time + Celery

def test_local_now_converts_aware_time_to_app_timezone(monkeypatch):
    monkeypatch.setattr(settings, "APP_TIMEZONE", "Europe/Istanbul")
    from datetime import UTC
    assert local_now(datetime(2026, 10, 5, 7, 0, tzinfo=UTC)) == datetime(2026, 10, 5, 10, 0)
    assert local_now(NOW) == NOW  # naive input is already local


def test_celery_beat_schedules_the_reminder_task():
    from app.workers.celery_app import celery_app
    import app.workers.tasks  # noqa: F401  - registers the task

    entry = celery_app.conf.beat_schedule["send-due-appointment-reminders"]
    assert entry["task"] == "reminders.send_due_reminders"
    assert entry["schedule"] == float(settings.REMINDER_SCAN_INTERVAL_SECONDS)
    assert "reminders.send_due_reminders" in celery_app.tasks
    assert celery_app.conf.timezone == settings.APP_TIMEZONE


def test_celery_task_runs_scan_and_closes_session():
    from app.workers import tasks

    fake_db = mock.MagicMock()
    report = delivery.DeliveryReport(sent=2, skipped=1)
    with mock.patch("app.db.session.SessionLocal", return_value=fake_db), \
         mock.patch("app.modules.reminders.delivery.send_due_reminders", return_value=report) as scan:
        result = tasks.send_due_reminders_task.run()
    scan.assert_called_once_with(fake_db)
    fake_db.close.assert_called_once()
    assert result == {"sent": 2, "failed": 0, "skipped": 1, "errors": []}


# ====================================================================== integration setup

class FakeMailer:
    def __init__(self, fail_times: int = 0):
        self.sent: list[dict] = []
        self.fail_times = fail_times
        self.lock = threading.Lock()

    def send(self, to_email, subject, html, text):
        with self.lock:
            if self.fail_times > 0:
                self.fail_times -= 1
                raise smtplib.SMTPServerDisconnected("connection lost")
            self.sent.append({"to": to_email, "subject": subject, "html": html, "text": text})

    def close(self):
        pass


@pytest.fixture(scope="module")
def engine():
    eng = make_engine()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def Session(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db(Session):
    session = Session()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def reminder_defaults(monkeypatch):
    monkeypatch.setattr(settings, "APP_TIMEZONE", "Europe/Istanbul")
    monkeypatch.setattr(settings, "REMINDER_MIN_LEAD_MINUTES", 60)
    monkeypatch.setattr(settings, "REMINDER_MAX_ATTEMPTS", 3)


class Shop:
    """One business with services, staff, branch and helpers to add rows."""

    def __init__(self, db, name="Kuaför", status=BusinessStatus.ACTIVE):
        sfx = uuid.uuid4().hex[:8]
        self.db = db
        self.business = Business(name=name, slug=f"shop-{sfx}", industry="beauty",
                                 email=f"shop-{sfx}@test.local", phone="000", status=status)
        db.add(self.business)
        db.flush()
        self.service = Service(business_id=self.business.id, name="Saç Kesimi", price=100, duration_minutes=30)
        self.staff = StaffProfile(business_id=self.business.id, full_name="Mehmet Usta")
        self.branch = Branch(business_id=self.business.id, name="Merkez", address="Atatürk Cad. 1")
        db.add_all([self.service, self.staff, self.branch])
        db.commit()

    def config(self, hours, active=True, channel=ReminderChannel.EMAIL,
               template="Sayın {{customer_name}}, {{appointment_date}} {{start_time}} {{service_name}} / {{staff_name}} @ {{branch_name}}"):
        c = ReminderConfig(business_id=self.business.id, channel=channel, hours_before=hours,
                           message_template=template, is_active=active)
        self.db.add(c)
        self.db.commit()
        return c

    def appointment(self, starts_in: timedelta, email="musteri@example.com",
                    status=AppointmentStatus.CONFIRMED, customer=None):
        start = NOW + starts_in
        a = Appointment(business_id=self.business.id, customer_name="Ayşe Kaya", customer_email=email,
                        customer_id=customer.id if customer else None,
                        service_id=self.service.id, staff_id=self.staff.id, branch_id=self.branch.id,
                        appointment_date=start.date(), start_time=start.time(),
                        end_time=(start + timedelta(minutes=30)).time(), status=status)
        self.db.add(a)
        self.db.commit()
        return a


@pytest.fixture
def shop(db, engine):
    # Each test starts with an empty reminder table so counts are exact.
    with engine.begin() as conn:
        conn.execute(ReminderLog.__table__.delete())
        conn.execute(ReminderConfig.__table__.delete())
        conn.execute(Appointment.__table__.delete())
    return Shop(db)


def logs_for(db, appointment):
    db.expire_all()
    return db.scalars(select(ReminderLog).where(ReminderLog.appointment_id == appointment.id)).all()


def run(db, at=NOW, mailer=None):
    mailer = mailer or FakeMailer()
    report = send_due_reminders(db, now=at, mailer=mailer)
    return report, mailer


# ====================================================================== integration: due rules

def test_no_config_sends_nothing(db, shop):
    shop.appointment(timedelta(hours=5))
    report, mailer = run(db)
    assert mailer.sent == [] and report.sent == 0


def test_due_appointment_gets_one_email_with_rendered_template(db, shop):
    shop.config(24)
    appt = shop.appointment(timedelta(hours=20))
    report, mailer = run(db)

    assert report.sent == 1 and len(mailer.sent) == 1
    mail = mailer.sent[0]
    assert mail["to"] == "musteri@example.com"
    assert mail["subject"] == "Randevu hatırlatması – Kuaför"
    start = NOW + timedelta(hours=20)
    assert format_date_tr(start.date()) in mail["text"]
    assert "Sayın Ayşe Kaya" in mail["text"]
    assert "Saç Kesimi / Mehmet Usta @ Merkez" in mail["text"]
    assert "Atatürk Cad. 1" in mail["text"]

    [log] = logs_for(db, appt)
    assert log.status == ReminderStatus.SENT
    assert log.recipient_email == "musteri@example.com"
    assert log.attempts == 1
    assert log.appointment_start == start
    assert log.sent_at is not None


def test_not_yet_due_and_past_appointments_are_ignored(db, shop):
    shop.config(24)
    later = shop.appointment(timedelta(hours=30))   # window opens in 6 h
    past = shop.appointment(-timedelta(hours=2))
    report, mailer = run(db)
    assert mailer.sent == []
    assert logs_for(db, later) == [] and logs_for(db, past) == []


def test_window_boundary_is_inclusive(db, shop):
    shop.config(24)
    shop.appointment(timedelta(hours=24))
    _, mailer = run(db)
    assert len(mailer.sent) == 1


@pytest.mark.parametrize("status", [AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW, AppointmentStatus.COMPLETED])
def test_closed_appointments_are_not_reminded(db, shop, status):
    shop.config(24)
    shop.appointment(timedelta(hours=5), status=status)
    _, mailer = run(db)
    assert mailer.sent == []


def test_pending_appointment_is_reminded(db, shop):
    shop.config(24)
    shop.appointment(timedelta(hours=5), status=AppointmentStatus.PENDING)
    _, mailer = run(db)
    assert len(mailer.sent) == 1


def test_deleted_appointment_is_not_reminded(db, shop):
    shop.config(24)
    appt = shop.appointment(timedelta(hours=5))
    appt.is_deleted = True
    db.commit()
    _, mailer = run(db)
    assert mailer.sent == []


def test_less_than_min_lead_gets_nothing(db, shop):
    shop.config(24)
    appt = shop.appointment(timedelta(minutes=45))
    _, mailer = run(db)
    assert mailer.sent == [] and logs_for(db, appt) == []


def test_inactive_and_sms_configs_are_ignored(db, shop):
    shop.config(24, active=False)
    shop.config(24, channel=ReminderChannel.SMS)
    shop.appointment(timedelta(hours=5))
    _, mailer = run(db)
    assert mailer.sent == []


def test_inactive_business_is_ignored(db, shop):
    shop.business.status = BusinessStatus.SUSPENDED
    db.commit()
    shop.config(24)
    shop.appointment(timedelta(hours=5))
    _, mailer = run(db)
    assert mailer.sent == []


# ====================================================================== integration: recipients

def test_missing_email_is_skipped_once_and_not_retried(db, shop):
    shop.config(24)
    appt = shop.appointment(timedelta(hours=5), email=None)
    report, mailer = run(db)
    assert mailer.sent == [] and report.skipped == 1
    [log] = logs_for(db, appt)
    assert log.status == ReminderStatus.SKIPPED and log.error_message == SKIP_NO_EMAIL

    report, mailer = run(db, at=NOW + timedelta(minutes=5))
    assert mailer.sent == [] and report.skipped == 0
    assert len(logs_for(db, appt)) == 1


def test_invalid_email_is_skipped(db, shop):
    shop.config(24)
    appt = shop.appointment(timedelta(hours=5), email="not-an-email")
    run(db)
    [log] = logs_for(db, appt)
    assert log.status == ReminderStatus.SKIPPED


def test_falls_back_to_customer_record_email(db, shop):
    customer = Customer(business_id=shop.business.id, name="Ayşe Kaya", email="kayit@example.com", phone="1")
    db.add(customer)
    db.commit()
    shop.config(24)
    shop.appointment(timedelta(hours=5), email=None, customer=customer)
    _, mailer = run(db)
    assert [m["to"] for m in mailer.sent] == ["kayit@example.com"]


# ====================================================================== integration: duplicates

def test_second_scan_does_not_send_again(db, shop):
    shop.config(24)
    appt = shop.appointment(timedelta(hours=20))
    run(db)
    report, mailer = run(db, at=NOW + timedelta(minutes=5))
    assert mailer.sent == [] and report.sent == 0
    assert len(logs_for(db, appt)) == 1


def test_parallel_workers_send_exactly_one_email(Session, shop):
    shop.config(24)
    appt = shop.appointment(timedelta(hours=20))
    mailer = FakeMailer()
    barrier = threading.Barrier(4)
    errors = []

    def worker():
        session = Session()
        try:
            barrier.wait()
            send_due_reminders(session, now=NOW, mailer=mailer)
        except Exception as exc:  # pragma: no cover - surfaced below
            errors.append(exc)
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert len(mailer.sent) == 1
    check = Session()
    assert len(logs_for(check, appt)) == 1
    check.close()


def test_unique_constraint_blocks_duplicate_rows(db, shop):
    config = shop.config(24)
    appt = shop.appointment(timedelta(hours=20))
    start = NOW + timedelta(hours=20)
    for _ in range(2):
        db.add(ReminderLog(business_id=shop.business.id, appointment_id=appt.id, reminder_config_id=config.id,
                           channel=ReminderChannel.EMAIL, appointment_start=start, status=ReminderStatus.SENT))
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


# ====================================================================== integration: retries

def test_failed_send_is_retried_until_success(db, shop):
    shop.config(24)
    appt = shop.appointment(timedelta(hours=20))
    mailer = FakeMailer(fail_times=1)

    report, _ = run(db, mailer=mailer)
    assert report.failed == 1
    [log] = logs_for(db, appt)
    assert log.status == ReminderStatus.FAILED and log.attempts == 1
    assert "connection lost" in log.error_message

    report, _ = run(db, at=NOW + timedelta(minutes=5), mailer=mailer)
    assert report.sent == 1 and len(mailer.sent) == 1
    [log] = logs_for(db, appt)
    assert log.status == ReminderStatus.SENT and log.attempts == 2


def test_retries_stop_after_max_attempts(db, shop):
    shop.config(24)
    appt = shop.appointment(timedelta(hours=20))
    mailer = FakeMailer(fail_times=99)
    for i in range(5):
        run(db, at=NOW + timedelta(minutes=5 * i), mailer=mailer)
    [log] = logs_for(db, appt)
    assert log.status == ReminderStatus.FAILED
    assert log.attempts == settings.REMINDER_MAX_ATTEMPTS
    assert mailer.fail_times == 99 - settings.REMINDER_MAX_ATTEMPTS


def test_one_failing_recipient_does_not_block_others(db, shop):
    shop.config(24)
    shop.appointment(timedelta(hours=10), email="a@example.com")
    shop.appointment(timedelta(hours=11), email="b@example.com")
    report, mailer = run(db, mailer=FakeMailer(fail_times=1))
    assert report.failed == 1 and report.sent == 1


# ====================================================================== integration: multiple configs

def test_two_configs_send_two_reminders_at_their_times(db, shop):
    shop.config(24)
    shop.config(2)
    appt = shop.appointment(timedelta(hours=23))

    _, first = run(db)                                      # 24 h window open
    _, second = run(db, at=NOW + timedelta(hours=10))       # still only 24 h
    _, third = run(db, at=NOW + timedelta(hours=21, minutes=30))  # 2 h window open

    assert len(first.sent) == 1 and second.sent == [] and len(third.sent) == 1
    assert sorted(l.status for l in logs_for(db, appt)) == [ReminderStatus.SENT, ReminderStatus.SENT]


def test_late_booking_sends_only_the_closest_config(db, shop):
    c24, c2 = shop.config(24), shop.config(2)
    appt = shop.appointment(timedelta(hours=1, minutes=30))   # both windows already open
    report, mailer = run(db)

    assert len(mailer.sent) == 1 and report.sent == 1 and report.skipped == 1
    logs = {l.reminder_config_id: l for l in logs_for(db, appt)}
    assert logs[c2.id].status == ReminderStatus.SENT
    assert logs[c24.id].status == ReminderStatus.SKIPPED and logs[c24.id].error_message == SKIP_SUPERSEDED

    _, again = run(db, at=NOW + timedelta(minutes=5))
    assert again.sent == []


def test_rescheduled_appointment_gets_a_new_reminder(db, shop):
    shop.config(24)
    appt = shop.appointment(timedelta(hours=20))
    run(db)

    new_start = NOW + timedelta(hours=22)
    appt.appointment_date, appt.start_time = new_start.date(), new_start.time()
    db.commit()
    _, mailer = run(db, at=NOW + timedelta(minutes=5))

    assert len(mailer.sent) == 1
    starts = sorted(l.appointment_start for l in logs_for(db, appt))
    assert starts == [NOW + timedelta(hours=20), new_start]


# ====================================================================== integration: tenants

def test_each_business_uses_only_its_own_configs(db, shop):
    other = Shop(db, name="Berber")
    shop.config(24, template="A: {{business_name}}")
    shop.appointment(timedelta(hours=5), email="a@example.com")
    other.appointment(timedelta(hours=5), email="b@example.com")   # Berber has no config

    _, mailer = run(db)
    assert [m["to"] for m in mailer.sent] == ["a@example.com"]
    assert mailer.sent[0]["text"].startswith("A: Kuaför")


def test_customer_email_from_another_business_is_not_used(db, shop):
    other = Shop(db, name="Berber")
    foreign = Customer(business_id=other.business.id, name="X", email="foreign@example.com", phone="1")
    db.add(foreign)
    db.commit()
    shop.config(24)
    appt = shop.appointment(timedelta(hours=5), email=None, customer=foreign)
    _, mailer = run(db)
    assert mailer.sent == []
    [log] = logs_for(db, appt)
    assert log.status == ReminderStatus.SKIPPED


# ====================================================================== integration: API

@pytest.fixture
def api(engine, db, shop):
    sfx = uuid.uuid4().hex[:8]
    owner = User(first_name="Owner", last_name="T", email=f"owner-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    outsider = User(first_name="Out", last_name="T", email=f"out-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    db.add_all([owner, outsider])
    db.flush()
    db.add(Membership(user_id=owner.id, business_id=shop.business.id, role=MembershipRole.OWNER))
    db.commit()
    with make_client(engine) as client:
        yield client, owner, outsider
    release_client()


def base(shop):
    return f"{API}/businesses/{shop.business.id}/reminders"


def test_api_rejects_sms_config(api, shop):
    client, owner, _ = api
    r = client.post(f"{base(shop)}/configs", headers=auth(owner),
                    json={"channel": "SMS", "hours_before": 24, "message_template": "x"})
    assert r.status_code == 422


def test_send_test_goes_only_to_logged_in_user(api, shop):
    client, owner, _ = api
    config = shop.config(24)
    with mock.patch("app.modules.reminders.service.SMTPClient.send") as send:
        r = client.post(f"{base(shop)}/send-test/{config.id}", headers=auth(owner),
                        json={"to_email": "someone-else@example.com"})
    assert r.status_code == 200, r.text
    assert r.json() == {"status": "sent", "recipient": owner.email}
    send.assert_called_once()
    sent = send.call_args.kwargs
    assert sent["to_email"] == owner.email
    assert sent["subject"].startswith("[TEST]")


def test_send_test_reports_smtp_failure(api, shop):
    client, owner, _ = api
    config = shop.config(24)
    with mock.patch("app.modules.reminders.service.SMTPClient.send", side_effect=smtplib.SMTPAuthenticationError(535, b"bad")):
        r = client.post(f"{base(shop)}/send-test/{config.id}", headers=auth(owner))
    assert r.status_code == 502


def test_send_test_and_logs_are_forbidden_for_other_businesses(api, shop):
    client, _, outsider = api
    config = shop.config(24)
    with mock.patch("app.modules.reminders.service.SMTPClient.send") as send:
        r = client.post(f"{base(shop)}/send-test/{config.id}", headers=auth(outsider))
    assert r.status_code == 403
    send.assert_not_called()
    assert client.get(f"{base(shop)}/logs", headers=auth(outsider)).status_code == 403


def test_logs_endpoint_returns_history_details(api, db, shop):
    client, owner, _ = api
    shop.config(24)
    shop.appointment(timedelta(hours=5))
    run(db)
    r = client.get(f"{base(shop)}/logs", headers=auth(owner))
    assert r.status_code == 200, r.text
    [row] = r.json()
    assert row["status"] == "SENT"
    assert row["customer_name"] == "Ayşe Kaya"
    assert row["hours_before"] == 24
    assert row["recipient_email"] == "musteri@example.com"
    assert row["attempts"] == 1
