"""
Public online booking page (/book/{slug}). PostgreSQL integration tests;
skipped when the database is unreachable.
"""
import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.appointments.models import Appointment
from app.modules.branches.models import Branch
from app.modules.business.models import Business
from app.modules.customers.models import Customer
from app.modules.services.models import Service
from app.modules.staff.models import StaffProfile
from app.shared.enums.service import ServiceStatus
from tests.pg_support import API, make_engine

TOMORROW = date.today() + timedelta(days=1)


@pytest.fixture(scope="module")
def engine():
    eng = make_engine()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture(scope="module")
def client(engine):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # raise_server_exceptions=False: a 500 must show up as a status code, like in the browser
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def shop(engine):
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    sfx = uuid.uuid4().hex[:8]

    def business(name):
        b = Business(name=name, slug=f"{name.lower()}-{sfx}", industry="beauty", email=f"{name.lower()}-{sfx}@t.local", phone="0")
        db.add(b)
        db.flush()
        return b

    w = type("Shop", (), {})()
    w.biz, w.other = business("Kuafor"), business("Rakip")
    w.service = Service(business_id=w.biz.id, name="Saç Kesimi", price=350, duration_minutes=30)
    w.inactive = Service(business_id=w.biz.id, name="Eski", price=1, duration_minutes=30, status=ServiceStatus.INACTIVE)
    w.branch = Branch(business_id=w.biz.id, name="Merkez")
    w.foreign_branch = Branch(business_id=w.other.id, name="Rakip Şube")
    w.foreign_staff = StaffProfile(business_id=w.other.id, full_name="Rakip Usta")
    db.add_all([w.service, w.inactive, w.branch, w.foreign_branch, w.foreign_staff])
    db.commit()
    w.db = db
    yield w
    db.close()


def book(client, shop, **overrides):
    body = {
        "customer_name": "Ali Veli",
        "customer_phone": "0555 123 45 67",
        "customer_email": "ali@example.com",
        "service_id": str(shop.service.id),
        "date": TOMORROW.isoformat(),
        "start_time": "10:00",
    }
    body.update(overrides)
    return client.post(f"{API}/public/booking/{shop.biz.slug}/book", json=body)


def appointments(shop):
    shop.db.expire_all()
    return shop.db.scalars(select(Appointment).where(Appointment.business_id == shop.biz.id)).all()


def test_booking_succeeds_and_creates_customer(client, shop):
    r = book(client, shop)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["date"] == TOMORROW.isoformat()
    assert data["start_time"] == "10:00:00" and data["end_time"] == "10:30:00"
    assert data["status"] == "PENDING"

    [appt] = appointments(shop)
    assert appt.customer_name == "Ali Veli" and appt.customer_email == "ali@example.com"
    assert appt.notes == "Online randevu sayfasından alındı."
    customer = shop.db.get(Customer, appt.customer_id)
    assert customer.business_id == shop.biz.id and customer.phone == "0555 123 45 67"


def test_existing_customer_is_matched_by_phone_digits(client, shop):
    existing = Customer(business_id=shop.biz.id, name="Ali Veli", phone="05551234567")
    shop.db.add(existing)
    shop.db.commit()
    r = book(client, shop, customer_phone="0555-123-45-67")
    assert r.status_code == 201, r.text
    assert r.json()["customer_id"] == str(existing.id)


def test_customer_of_another_business_is_not_reused(client, shop):
    foreign = Customer(business_id=shop.other.id, name="X", phone="05551234567")
    shop.db.add(foreign)
    shop.db.commit()
    r = book(client, shop)
    assert r.status_code == 201
    assert r.json()["customer_id"] != str(foreign.id)


def test_same_slot_cannot_be_booked_twice(client, shop):
    assert book(client, shop).status_code == 201
    r = book(client, shop, customer_phone="05559999999")
    assert r.status_code == 409
    assert "müsait değil" in r.json()["message"]
    assert len(appointments(shop)) == 1


def test_past_day_is_rejected(client, shop):
    r = book(client, shop, date=(date.today() - timedelta(days=1)).isoformat())
    assert r.status_code == 409
    assert appointments(shop) == []


def test_inactive_service_is_rejected(client, shop):
    assert book(client, shop, service_id=str(shop.inactive.id)).status_code == 404


def test_branch_or_staff_of_another_business_is_rejected(client, shop):
    assert book(client, shop, branch_id=str(shop.foreign_branch.id)).status_code == 404
    assert book(client, shop, staff_id=str(shop.foreign_staff.id)).status_code == 404
    r = client.get(f"{API}/public/booking/{shop.biz.slug}/available-slots",
                   params={"date": TOMORROW.isoformat(), "service_id": str(shop.service.id),
                           "staff_id": str(shop.foreign_staff.id)})
    assert r.status_code == 404
    assert appointments(shop) == []


def test_own_branch_is_accepted(client, shop):
    r = book(client, shop, branch_id=str(shop.branch.id))
    assert r.status_code == 201, r.text
    assert r.json()["branch_id"] == str(shop.branch.id)


def test_unknown_business(client, shop):
    r = client.post(f"{API}/public/booking/yok-boyle-bir-isletme/book", json={
        "customer_name": "A", "customer_phone": "1", "service_id": str(shop.service.id),
        "date": TOMORROW.isoformat(), "start_time": "10:00"})
    assert r.status_code == 404
