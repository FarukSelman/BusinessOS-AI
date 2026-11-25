"""
Appointment create, list, cancel, complete and available slots through the
real API.

These tests used to call /api/v1/appointments and /appointments/slots, paths
that never existed (appointments live under
/businesses/{business_id}/appointments, slots at /available-slots), sent a
title/start_time/end_time body the API does not take, and patched a service
the route never used. They now run against PostgreSQL (skipped when it is
unreachable).
"""
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.modules.business.models import Business
from app.modules.membership.models import Membership
from app.modules.user.models import User
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


@pytest.fixture
def w(db):
    sfx = uuid.uuid4().hex[:8]
    w = World()
    w.biz = Business(name="Kuaför", slug=f"ap-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    w.user = User(first_name="Owner", last_name="Test", email=f"o-{sfx}@test.local", password_hash="x",
                  status=UserStatus.ACTIVE)
    db.add_all([w.biz, w.user])
    db.flush()
    db.add(Membership(user_id=w.user.id, business_id=w.biz.id, role=MembershipRole.OWNER))
    db.commit()
    w.url = f"{API}/businesses/{w.biz.id}/appointments"
    # A week ahead, so no slot of that day is already in the past.
    w.day = datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date() + timedelta(days=7)
    return w


@pytest.fixture
def appointment_data(w):
    return {
        "customer_name": "Ayşe Kaya",
        "customer_phone": "0555 111 22 33",
        "appointment_date": w.day.isoformat(),
        "start_time": "10:00",
        "end_time": "11:00",
        "notes": "Consultation",
    }


@pytest.fixture
def appointment(client, w, appointment_data):
    res = client.post(w.url, json=appointment_data, headers=auth(w.user))
    assert res.status_code == 201, res.text
    return res.json()


def test_create_appointment(client, w, appointment_data):
    """Test creating an appointment."""
    response = client.post(w.url, json=appointment_data, headers=auth(w.user))
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["customer_name"] == "Ayşe Kaya" and body["status"] == "PENDING"
    assert body["appointment_date"] == w.day.isoformat() and body["start_time"].startswith("10:00")


def test_list_appointments(client, w, appointment):
    """Test listing appointments."""
    response = client.get(w.url, headers=auth(w.user))
    assert response.status_code == 200
    assert [a["id"] for a in response.json()] == [appointment["id"]]


def test_cancel_appointment(client, w, appointment):
    """Test canceling an appointment."""
    response = client.post(f"{w.url}/{appointment['id']}/cancel", headers=auth(w.user))
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "CANCELLED"


def test_complete_appointment(client, w, appointment):
    """Test completing an appointment."""
    response = client.post(f"{w.url}/{appointment['id']}/complete", headers=auth(w.user))
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "COMPLETED"


def test_get_available_slots(client, w, appointment):
    """Test getting available slots: the booked hour is not offered."""
    response = client.get(f"{w.url}/available-slots", params={"date": w.day.isoformat()}, headers=auth(w.user))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["date"] == w.day.isoformat()
    slots = body["available_slots"]
    assert slots and "09:00" in slots
    assert "10:00" not in slots  # taken by the appointment


def test_appointments_require_authentication(client, w, appointment_data):
    assert client.post(w.url, json=appointment_data).status_code == 401
    assert client.get(w.url).status_code == 401
