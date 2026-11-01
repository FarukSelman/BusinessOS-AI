"""
Calendar view: GET /appointments/range.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import date, time

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.appointments.models import Appointment
from app.modules.branches.models import Branch
from app.modules.business.models import Business
from app.modules.membership.models import Membership
from app.modules.staff.models import StaffProfile
from app.modules.user.models import User
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client


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


def make_world(db) -> World:
    sfx = uuid.uuid4().hex[:8]
    w = World()
    w.owner = User(first_name="Owner", last_name="X", email=f"o-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    db.add(w.owner)
    db.flush()
    w.biz = Business(name="Takvim Kuaför", slug=f"takvim-{sfx}", industry="beauty", email=f"b-{sfx}@t.local", phone="0")
    db.add(w.biz)
    db.flush()
    db.add(Membership(user_id=w.owner.id, business_id=w.biz.id, role=MembershipRole.OWNER))
    w.branch_a = Branch(business_id=w.biz.id, name="Merkez")
    w.branch_b = Branch(business_id=w.biz.id, name="Şube 2")
    db.add_all([w.branch_a, w.branch_b])
    db.flush()
    w.ayse = StaffProfile(business_id=w.biz.id, full_name="Ayşe", branch_id=w.branch_a.id)
    w.mehmet = StaffProfile(business_id=w.biz.id, full_name="Mehmet", branch_id=w.branch_b.id)
    db.add_all([w.ayse, w.mehmet])
    db.flush()

    def appt(d, hour, staff, branch, status=AppointmentStatus.CONFIRMED, deleted=False):
        a = Appointment(business_id=w.biz.id, customer_name=f"Müşteri {d}-{hour}", customer_phone="05550000000",
                        staff_id=staff.id, branch_id=branch.id, appointment_date=d, start_time=time(hour),
                        end_time=time(hour + 1), status=status, notes="gizli not", is_deleted=deleted)
        db.add(a)
        return a

    appt(date(2026, 10, 31), 10, w.ayse, w.branch_a)             # day before the range
    w.in1 = appt(date(2026, 11, 1), 14, w.ayse, w.branch_a)
    w.in2 = appt(date(2026, 11, 1), 9, w.mehmet, w.branch_b)
    w.in3 = appt(date(2026, 11, 30), 11, w.ayse, w.branch_a, status=AppointmentStatus.CANCELLED)
    appt(date(2026, 11, 15), 12, w.ayse, w.branch_a, deleted=True)
    appt(date(2026, 12, 1), 10, w.mehmet, w.branch_b)            # day after the range
    db.commit()
    return w


def get_range(client, w, user=None, **params):
    params = {"start": "2026-11-01", "end": "2026-11-30", **params}
    return client.get(f"{API}/businesses/{w.biz.id}/appointments/range", params=params, headers=auth(user or w.owner))


def test_returns_only_the_range_sorted_and_without_deleted(client, db):
    w = make_world(db)
    res = get_range(client, w)
    assert res.status_code == 200
    ids = [a["id"] for a in res.json()]
    assert ids == [str(w.in2.id), str(w.in1.id), str(w.in3.id)]


def test_rows_are_lightweight(client, db):
    w = make_world(db)
    row = get_range(client, w).json()[0]
    assert set(row) == {"id", "customer_name", "service_id", "staff_id", "branch_id",
                        "appointment_date", "start_time", "end_time", "status"}


def test_staff_and_branch_filters_combine(client, db):
    w = make_world(db)
    assert {a["id"] for a in get_range(client, w, staff_id=str(w.ayse.id)).json()} == {str(w.in1.id), str(w.in3.id)}
    assert [a["id"] for a in get_range(client, w, branch_id=str(w.branch_b.id)).json()] == [str(w.in2.id)]
    # Ayşe works at branch A, so Ayşe + branch B is empty (the old list endpoint ignored the branch).
    assert get_range(client, w, staff_id=str(w.ayse.id), branch_id=str(w.branch_b.id)).json() == []


def test_status_filter_is_repeatable(client, db):
    w = make_world(db)
    res = get_range(client, w, status=["CONFIRMED", "PENDING"])
    assert {a["id"] for a in res.json()} == {str(w.in1.id), str(w.in2.id)}


def test_range_is_limited_to_42_days(client, db):
    w = make_world(db)
    assert get_range(client, w, start="2026-11-01", end="2026-12-12").status_code == 200  # 42 days
    assert get_range(client, w, start="2026-11-01", end="2026-12-13").status_code == 400  # 43 days
    assert get_range(client, w, start="2026-11-30", end="2026-11-01").status_code == 400


def test_other_business_cannot_read_the_calendar(client, db):
    w = make_world(db)
    other = make_world(db)
    assert get_range(client, w, user=other.owner).status_code in (403, 404)
