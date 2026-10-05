"""
Dashboard "AI İçgörüleri".

A fake language model replaces OpenAI, so nothing leaves the machine.
Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import json
import uuid
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.modules.appointments.models import Appointment
from app.modules.business.models import Business
from app.modules.customers.models import Customer
from app.modules.expenses.models import Expense
from app.modules.insights import generator, service as insight_service
from app.modules.insights.metrics import build_metrics, pct_change, periods
from app.modules.insights.models import BusinessInsight, InsightStatus, InsightTrigger
from app.modules.invoice.models import Invoice
from app.modules.membership.models import Membership
from app.modules.services.models import Service
from app.modules.staff.models import StaffProfile
from app.modules.user.models import User
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.business import BusinessStatus
from app.shared.enums.expense import TransactionDirection
from app.shared.enums.invoice import InvoiceStatus
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

TODAY = insight_service.local_today()

GOOD_ANSWER = {
    "summary": "Gelir düştü, iptaller arttı.",
    "items": [
        {"type": "negative", "title": "Gelir düştü", "detail": "Muhtemel sebep iptallerin artması.", "metric": "revenue"},
        {"type": "negative", "title": "İptaller arttı", "detail": "İptal oranı yükseldi.", "metric": "cancel_rate"},
        {"type": "positive", "title": "Yeni müşteriler", "detail": "Yeni müşteri sayısı arttı.", "metric": "new_customers"},
        {"type": "suggestion", "title": "Sakin güne kampanya", "detail": "En sakin güne indirim yapın.", "metric": "quietest_weekday"},
    ],
}


class FakeModel:
    def __init__(self, answer=None, error: Exception | None = None):
        self.answer = GOOD_ANSWER if answer is None else answer
        self.error = error
        self.calls: list[dict] = []

    def chat_json(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.answer if isinstance(self.answer, str) else json.dumps(self.answer, ensure_ascii=False)


# ====================================================================== unit

def test_periods_are_two_equal_30_day_windows():
    current, previous = periods(date(2026, 10, 5))
    assert (current.start, current.end) == (date(2026, 9, 6), date(2026, 10, 5))
    assert (previous.start, previous.end) == (date(2026, 8, 7), date(2026, 9, 5))
    assert (current.end - current.start).days == (previous.end - previous.start).days == 29


def test_pct_change():
    assert pct_change(85, 100) == -15.0
    assert pct_change(150, 100) == 50.0
    assert pct_change(10, 0) is None


METRICS = {
    "current": {"revenue": 8500.0, "expenses": 1000.0, "net": 7500.0, "average_ticket": 425.0, "new_customers": 6,
                "appointments": {"total": 40, "completed": 30, "cancelled": 8, "cancel_rate": 20.0,
                                 "no_show_rate": 2.5, "online_share": 35.0}},
    "changes": {"revenue_pct": -15.0, "cancel_rate_pp": 7.5, "new_customers_pct": 50.0, "appointments_pct": None},
    "top_services": [{"service": "Saç Kesimi", "appointments": 22}],
    "quietest_weekday": "Salı", "busiest_weekday": "Cumartesi",
    "pending_appointment_approvals": 2, "pending_agent_drafts": 1,
}


def test_badges_are_computed_from_metrics_not_model_text():
    assert generator.badge_for("revenue", METRICS) == "Gelir −%15"
    assert generator.badge_for("cancel_rate", METRICS) == "İptal %20 (+7,5 puan)"
    assert generator.badge_for("new_customers", METRICS) == "Yeni müşteri +%50"
    assert generator.badge_for("appointments", METRICS) == "Randevu 40"  # no base -> plain number
    assert generator.badge_for("top_service", METRICS) == "Saç Kesimi · 22"
    assert generator.badge_for("pending", METRICS) == "Onay bekleyen 3"
    assert generator.badge_for("none", METRICS) is None


def test_validation_keeps_max_four_findings_and_one_suggestion():
    answer = {"summary": "Özet", "items": [
        {"type": "positive", "title": f"B{i}", "detail": "d", "metric": "revenue"} for i in range(6)
    ] + [{"type": "suggestion", "title": "Ö1", "detail": "d", "metric": "none"},
         {"type": "suggestion", "title": "Ö2", "detail": "d", "metric": "none"}]}
    result = generator.parse_and_validate(json.dumps(answer), METRICS)
    assert [i["type"] for i in result.items] == ["positive"] * 4 + ["suggestion"]
    assert result.items[-1]["title"] == "Ö1"


def test_validation_rejects_bad_answers():
    with pytest.raises(generator.InvalidInsight):
        generator.parse_and_validate("not json", METRICS)
    with pytest.raises(generator.InvalidInsight):  # only one valid finding
        generator.parse_and_validate(json.dumps({"summary": "x", "items": [
            {"type": "positive", "title": "a", "detail": "b", "metric": "revenue"},
            {"type": "weird", "title": "a", "detail": "b", "metric": "revenue"}]}), METRICS)
    with pytest.raises(generator.InvalidInsight):
        generator.parse_and_validate(json.dumps({"summary": "", "items": GOOD_ANSWER["items"]}), METRICS)


def test_unknown_metric_becomes_none_and_long_text_is_cut():
    answer = {"summary": "s", "items": [
        {"type": "neutral", "title": "T" * 200, "detail": "D " * 400, "metric": "hacked"},
        {"type": "neutral", "title": "ok", "detail": "ok", "metric": "revenue"}]}
    result = generator.parse_and_validate(json.dumps(answer), METRICS)
    assert result.items[0]["metric"] == "none" and result.items[0]["badge"] is None
    assert len(result.items[0]["title"]) <= 80 and len(result.items[0]["detail"]) <= 320


def test_schema_is_strict():
    assert generator.SCHEMA["additionalProperties"] is False
    item = generator.SCHEMA["properties"]["items"]["items"]
    assert item["additionalProperties"] is False and set(item["required"]) == {"type", "title", "detail", "metric"}


def test_celery_beat_runs_insights_at_three():
    from app.workers.celery_app import celery_app
    import app.workers.tasks  # noqa: F401

    entry = celery_app.conf.beat_schedule["generate-business-insights-nightly"]
    assert entry["task"] == "insights.generate_all" and "insights.generate_all" in celery_app.tasks
    assert entry["schedule"].hour == {3} and entry["schedule"].minute == {0}


# ====================================================================== integration

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
    s = Session()
    yield s
    s.close()


@pytest.fixture
def fake(monkeypatch, Session):
    model = FakeModel()
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key-not-used")
    monkeypatch.setattr(insight_service, "get_insights_client", lambda: model)
    monkeypatch.setattr(insight_service, "SESSION_FACTORY", Session)
    return model


@pytest.fixture
def client(engine, fake):
    with make_client(engine) as c:
        yield c
    release_client()


SECRET_NAMES = ["Zeliha Gizlioğlu", "Ahmet Saklıbey"]
SECRET_PHONES = ["05559876543", "05551112299"]
SECRET_EMAILS = ["zeliha.gizli@example.com", "ahmet.sakli@example.com"]
SECRET_STAFF = ["Gizem Ustaoğlu", "Kerem Makasçı"]
SECRET_NOTE = "Müşteri alerjik, gizli not"


class World:
    pass


def make_world(db, with_history=True) -> World:
    sfx = uuid.uuid4().hex[:8]
    w = World()
    w.owner = User(first_name="Owner", last_name="X", email=f"o-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    w.employee = User(first_name="Emp", last_name="X", email=f"e-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    w.viewer = User(first_name="View", last_name="X", email=f"v-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    db.add_all([w.owner, w.employee, w.viewer])
    db.flush()
    w.biz = Business(name="Gizli Kuaför", slug=f"gizli-{sfx}", industry="beauty", email=f"b-{sfx}@t.local", phone="0")
    db.add(w.biz)
    db.flush()
    db.add_all([
        Membership(user_id=w.owner.id, business_id=w.biz.id, role=MembershipRole.OWNER),
        Membership(user_id=w.employee.id, business_id=w.biz.id, role=MembershipRole.EMPLOYEE),
        Membership(user_id=w.viewer.id, business_id=w.biz.id, role=MembershipRole.VIEWER),
    ])
    if not with_history:
        db.commit()
        return w

    w.service = Service(business_id=w.biz.id, name="Saç Kesimi", price=500, duration_minutes=60)
    w.color = Service(business_id=w.biz.id, name="Boya", price=1500, duration_minutes=120)
    db.add_all([w.service, w.color])
    staff = [StaffProfile(business_id=w.biz.id, full_name=n, phone="05000000000", email=f"{i}@staff.test")
             for i, n in enumerate(SECRET_STAFF)]
    db.add_all(staff)
    db.flush()
    customers = [Customer(business_id=w.biz.id, name=n, phone=p, email=e)
                 for n, p, e in zip(SECRET_NAMES, SECRET_PHONES, SECRET_EMAILS)]
    db.add_all(customers)
    db.flush()

    def appt(days_ago, status, cust=0, svc=None, staff_i=0, hour=10):
        d = TODAY - timedelta(days=days_ago)
        c = customers[cust]
        a = Appointment(business_id=w.biz.id, customer_id=c.id, customer_name=c.name, customer_phone=c.phone,
                        customer_email=c.email, service_id=(svc or w.service).id, staff_id=staff[staff_i].id,
                        appointment_date=d, start_time=time(hour), end_time=time(hour + 1), status=status,
                        notes=SECRET_NOTE)
        db.add(a)
        return a

    # previous window (31..59 days ago): 10 appointments, 1 cancelled, revenue 5000
    for i in range(10):
        appt(31 + i, AppointmentStatus.CANCELLED if i == 0 else AppointmentStatus.COMPLETED, cust=i % 2, staff_i=i % 2)
    # current window (0..29 days ago): 10 appointments, 3 cancelled, revenue 4250 (-15%)
    for i in range(10):
        appt(1 + i, AppointmentStatus.CANCELLED if i < 3 else AppointmentStatus.COMPLETED, cust=i % 2,
             svc=w.color if i == 9 else None, staff_i=i % 2, hour=10 + i % 3)

    def invoice(days_ago, amount, n):
        paid = datetime.combine(TODAY - timedelta(days=days_ago), time(12), tzinfo=UTC)
        db.add(Invoice(business_id=w.biz.id, customer_id=customers[0].id, customer_name=SECRET_NAMES[0],
                       invoice_number=f"INV-{sfx}-{n}", items=[], subtotal=Decimal(amount), tax_rate=0, tax_amount=0,
                       total_amount=Decimal(amount), status=InvoiceStatus.PAID, paid_at=paid))

    invoice(35, "5000", 1)
    invoice(3, "4250", 2)
    db.add(Expense(business_id=w.biz.id, direction=TransactionDirection.EXPENSE, title="Kira",
                   amount=Decimal("1000"), transaction_date=TODAY - timedelta(days=2)))
    db.commit()
    return w


def test_metrics_are_correct_and_compare_equal_windows(db):
    w = make_world(db)
    m = build_metrics(db, w.biz.id, TODAY)
    assert m["current"]["revenue"] == 4250.0 and m["previous"]["revenue"] == 5000.0
    assert m["changes"]["revenue_pct"] == -15.0
    assert m["current"]["appointments"]["cancelled"] == 3 and m["current"]["appointments"]["cancel_rate"] == 30.0
    assert m["changes"]["cancel_rate_pp"] == 20.0
    assert m["current"]["expenses"] == 1000.0 and m["current"]["net"] == 3250.0
    assert m["top_services"][0]["service"] == "Saç Kesimi"
    assert {s["label"] for s in m["staff"]} == {"Personel A", "Personel B"}


def test_nothing_personal_is_sent_to_the_model(db):
    """The exact text sent to the model must not contain any personal data."""
    w = make_world(db)
    prompt = generator.build_user_prompt(build_metrics(db, w.biz.id, TODAY)) + generator.SYSTEM_PROMPT
    for secret in SECRET_NAMES + SECRET_PHONES + SECRET_EMAILS + SECRET_STAFF + [SECRET_NOTE]:
        assert secret not in prompt, secret
    for fragment in ["Zeliha", "Ahmet", "Gizem", "Kerem", "@", "0555", "alerjik"]:
        assert fragment not in prompt, fragment
    assert "Personel A" in prompt and "Saç Kesimi" in prompt


def test_single_staff_member_is_not_reported(db):
    w = make_world(db)
    db.query(Appointment).filter(Appointment.business_id == w.biz.id).update({"staff_id": None})
    db.commit()
    assert build_metrics(db, w.biz.id, TODAY)["staff"] == []


def test_new_business_gets_insufficient_data_without_calling_the_model(db, fake):
    w = make_world(db, with_history=False)
    row = insight_service.InsightService(db).generate_now(w.biz.id, InsightTrigger.MANUAL)
    assert row.status == InsightStatus.INSUFFICIENT_DATA
    assert row.metrics["appointments_60d"] == 0 and row.metrics["required_appointments"] == 5
    assert fake.calls == []


def test_first_view_generates_in_background_then_serves_the_stored_insight(client, db, fake):
    w = make_world(db)
    r = client.get(f"{API}/businesses/{w.biz.id}/insights", headers=auth(w.owner))
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "generating"  # background task runs after the response

    r = client.get(f"{API}/businesses/{w.biz.id}/insights", headers=auth(w.owner))
    body = r.json()
    assert body["state"] == "ready", body
    assert body["summary"] == "Gelir düştü, iptaller arttı."
    assert [i["type"] for i in body["items"]] == ["negative", "negative", "positive", "suggestion"]
    assert body["items"][0]["badge"] == "Gelir −%15"
    assert body["items"][1]["badge"] == "İptal %30 (+20 puan)"
    assert body["stale"] is False and body["can_refresh"] is True
    assert "metrics" not in body

    client.get(f"{API}/businesses/{w.biz.id}/insights", headers=auth(w.owner))
    assert len(fake.calls) == 1  # no second generation the same day


def test_model_error_keeps_dashboard_working(client, db, fake):
    w = make_world(db)
    fake.error = TimeoutError("OpenAI did not answer")
    client.get(f"{API}/businesses/{w.biz.id}/insights", headers=auth(w.owner))
    body = client.get(f"{API}/businesses/{w.biz.id}/insights", headers=auth(w.owner)).json()
    assert body["state"] == "unavailable" and body["items"] == []
    row = db.scalar(select(BusinessInsight).where(BusinessInsight.business_id == w.biz.id))
    assert row.status == InsightStatus.FAILED and "TimeoutError" in row.error

    # within 10 minutes a failure is not retried on every visit
    client.get(f"{API}/businesses/{w.biz.id}/insights", headers=auth(w.owner))
    assert len(fake.calls) == 1


def test_failure_after_success_keeps_the_previous_insight(db, fake):
    w = make_world(db)
    service = insight_service.InsightService(db)
    service.generate_now(w.biz.id, InsightTrigger.NIGHTLY)
    fake.answer = "{broken json"
    failed = service.generate_now(w.biz.id, InsightTrigger.MANUAL)
    assert failed.status == InsightStatus.FAILED
    state = service.state(w.biz.id)
    assert state.state == "ready" and state.shown.summary == "Gelir düştü, iptaller arttı."
    assert state.last_attempt_failed is True


def test_refresh_is_limited_to_once_per_hour(client, db, fake):
    w = make_world(db)
    url = f"{API}/businesses/{w.biz.id}/insights/refresh"
    first = client.post(url, headers=auth(w.owner))
    assert first.status_code == 202, first.text
    second = client.post(url, headers=auth(w.owner))
    assert second.status_code == 429
    assert "saatte bir" in second.json()["message"]
    body = client.get(f"{API}/businesses/{w.biz.id}/insights", headers=auth(w.owner)).json()
    assert body["can_refresh"] is False and body["next_refresh_at"]


@pytest.mark.parametrize("role", ["employee", "viewer"])
def test_insights_are_owner_admin_only(client, db, role):
    w = make_world(db)
    user = getattr(w, role)
    assert client.get(f"{API}/businesses/{w.biz.id}/insights", headers=auth(user)).status_code == 403
    assert client.post(f"{API}/businesses/{w.biz.id}/insights/refresh", headers=auth(user)).status_code == 403


def test_other_business_cannot_read_insights(client, db):
    w, other = make_world(db), make_world(db, with_history=False)
    assert client.get(f"{API}/businesses/{w.biz.id}/insights", headers=auth(other.owner)).status_code == 403


def test_not_configured_shows_message_and_never_generates(client, db, fake, monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    w = make_world(db)
    body = client.get(f"{API}/businesses/{w.biz.id}/insights", headers=auth(w.owner)).json()
    assert body["state"] == "not_configured" and body["can_refresh"] is False
    assert client.post(f"{API}/businesses/{w.biz.id}/insights/refresh", headers=auth(w.owner)).status_code == 503
    assert db.scalar(select(BusinessInsight).where(BusinessInsight.business_id == w.biz.id)) is None


def test_crashed_generation_does_not_block_forever(db, fake):
    w = make_world(db)
    db.add(BusinessInsight(business_id=w.biz.id, status=InsightStatus.GENERATING, trigger=InsightTrigger.FIRST_VIEW,
                           period_start=TODAY, period_end=TODAY,
                           created_at=datetime.now(UTC) - timedelta(minutes=15)))
    db.commit()
    service = insight_service.InsightService(db)
    assert service.state(w.biz.id).generating is False
    assert service.generate_now(w.biz.id, InsightTrigger.MANUAL).status == InsightStatus.READY


def test_nightly_job_covers_active_businesses_only(db, fake):
    active, empty, suspended = make_world(db), make_world(db, with_history=False), make_world(db)
    suspended.biz.status = BusinessStatus.SUSPENDED
    db.commit()
    report = insight_service.generate_for_all_businesses(db)
    rows = {r.business_id: r for r in db.scalars(select(BusinessInsight).where(BusinessInsight.trigger == InsightTrigger.NIGHTLY))}
    assert rows[active.biz.id].status == InsightStatus.READY
    assert rows[empty.biz.id].status == InsightStatus.INSUFFICIENT_DATA
    assert suspended.biz.id not in rows
    assert report["ready"] >= 1 and report["insufficient_data"] >= 1


# ---------------------------------------------------------------- finance visibility in reports

def test_finance_numbers_hidden_from_employee_and_viewer(client, db):
    w = make_world(db)
    base = f"{API}/businesses/{w.biz.id}/reports"
    owner_stats = client.get(f"{base}/dashboard-stats", headers=auth(w.owner)).json()
    assert owner_stats["total_revenue_this_month"] is not None

    for user in (w.employee, w.viewer):
        stats = client.get(f"{base}/dashboard-stats", headers=auth(user))
        assert stats.status_code == 200
        body = stats.json()
        assert body["total_revenue_this_month"] is None and body["net_profit_this_month"] is None
        assert body["total_customers"] == 2  # non-finance numbers still there
        assert client.get(f"{base}/revenue", headers=auth(user)).status_code == 403
        services = client.get(f"{base}/services", headers=auth(user)).json()
        assert services and all(s["revenue"] is None for s in services)
        staff = client.get(f"{base}/staff-performance", headers=auth(user)).json()
        assert staff and all(s["revenue"] is None for s in staff)
        customers = client.get(f"{base}/customers", headers=auth(user)).json()
        assert all(c.get("total_spent") is None for c in customers["top_customers"])
        appointments = client.get(f"{base}/appointments", headers=auth(user)).json()
        assert all(s["revenue"] is None for s in appointments["by_service"])

    assert client.get(f"{base}/revenue", headers=auth(w.owner)).status_code == 200
