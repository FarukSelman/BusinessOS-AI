"""
Visit stats on customer rows, the min_visits filter, a customer's full history
and customer names on the loyalty wallet list.

The customers page used to compute "AI Analizi" from the business's latest 200
appointments and the history tab from the latest 20, so older customers looked
like they had never come. Stats now come from the backend per customer.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.modules.appointments.models import Appointment
from app.modules.business.models import Business
from app.modules.customers.models import Customer
from app.modules.loyalty.models import LoyaltyWallet
from app.modules.membership.models import Membership
from app.modules.user.models import User
from app.shared.enums.appointment import AppointmentStatus as S
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

NEWER_APPOINTMENTS = 210  # more than the old 200 (insight) and 20 (history) windows


@pytest.fixture(scope="module")
def engine():
    eng = make_engine()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine):
    s = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield s
    s.close()


@pytest.fixture
def client(engine):
    with make_client(engine) as c:
        yield c
    release_client()


class World:
    pass


@pytest.fixture
def w(db):
    sfx = uuid.uuid4().hex[:8]
    w = World()
    w.today = datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date()
    w.biz = Business(name="Ziyaret", slug=f"zi-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    w.owner = User(first_name="O", last_name="X", email=f"o-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    db.add(w.owner)
    db.flush()
    db.add(Membership(user_id=w.owner.id, business_id=w.biz.id, role=MembershipRole.OWNER))

    w.loyal = Customer(business_id=w.biz.id, name="Eski Müşteri")
    w.busy = Customer(business_id=w.biz.id, name="Yoğun Müşteri")
    w.new = Customer(business_id=w.biz.id, name="Yeni Müşteri")
    db.add_all([w.loyal, w.busy, w.new])
    db.flush()

    def appt(customer, days_ago, status):
        return Appointment(business_id=w.biz.id, customer_id=customer.id, customer_name=customer.name,
                           appointment_date=w.today - timedelta(days=days_ago), start_time=time(10), status=status)

    # The loyal customer came long ago: 3 completed visits a year back, one
    # no-show, one cancelled later on and one upcoming booking.
    w.loyal_last_visit = w.today - timedelta(days=360)
    db.add_all([
        appt(w.loyal, 400, S.COMPLETED),
        appt(w.loyal, 380, S.COMPLETED),
        appt(w.loyal, 360, S.COMPLETED),
        appt(w.loyal, 370, S.NO_SHOW),
        appt(w.loyal, 100, S.CANCELLED),
        appt(w.loyal, -7, S.CONFIRMED),
    ])
    # Someone else fills the recent calendar.
    db.add_all([appt(w.busy, i % 300, S.COMPLETED if i % 2 else S.CONFIRMED) for i in range(NEWER_APPOINTMENTS)])
    db.add(LoyaltyWallet(business_id=w.biz.id, customer_id=w.loyal.id, balance=50))
    db.commit()
    return w


def get(client, w, path, **params):
    res = client.get(f"{API}/businesses/{w.biz.id}{path}", params=params, headers=auth(w.owner))
    assert res.status_code == 200, res.text
    return res


def rows_by_name(client, w, **params):
    return {c["name"]: c for c in get(client, w, "/customers", size=50, **params).json()}


def test_list_rows_carry_visit_stats_of_old_customers(client, w):
    rows = rows_by_name(client, w)
    loyal = rows["Eski Müşteri"]
    assert loyal["completed_visits"] == 3
    # not the cancelled one, not the upcoming one; a no-show earlier than the last completed one
    assert loyal["last_visit_date"] == w.loyal_last_visit.isoformat()
    assert rows["Yeni Müşteri"]["completed_visits"] == 0 and rows["Yeni Müşteri"]["last_visit_date"] is None
    assert rows["Yoğun Müşteri"]["completed_visits"] == NEWER_APPOINTMENTS // 2


def test_single_customer_carries_visit_stats(client, w):
    c = get(client, w, f"/customers/{w.loyal.id}").json()
    assert c["completed_visits"] == 3 and c["last_visit_date"] == w.loyal_last_visit.isoformat()
    assert c["tags"] == []


def test_min_visits_filters_on_completed_appointments(client, w):
    res = get(client, w, "/customers", min_visits=3)
    assert sorted(c["name"] for c in res.json()) == ["Eski Müşteri", "Yoğun Müşteri"]
    assert res.headers["X-Total-Count"] == "2"
    assert set(rows_by_name(client, w, min_visits=4)) == {"Yoğun Müşteri"}
    assert len(rows_by_name(client, w, min_visits=1)) == 2


def test_min_visits_rejects_zero(client, w):
    res = client.get(f"{API}/businesses/{w.biz.id}/customers", params={"min_visits": 0}, headers=auth(w.owner))
    assert res.status_code == 422


def test_history_has_every_appointment_of_the_customer(client, w):
    history = get(client, w, f"/customers/{w.loyal.id}/history").json()
    dates = [a["appointment_date"] for a in history["appointments"]]
    assert len(dates) == 6
    assert dates == sorted(dates, reverse=True)  # newest first
    assert all(a["customer_id"] == str(w.loyal.id) for a in history["appointments"])


def test_wallet_list_carries_customer_name(client, w):
    wallets = get(client, w, "/loyalty/wallets").json()
    assert [(x["customer_name"], x["balance"]) for x in wallets] == [("Eski Müşteri", 50)]
