"""
Global search (Ctrl+K): GET /businesses/{id}/search?q=

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.appointments.models import Appointment
from app.modules.business.models import Business
from app.modules.customers.models import Customer
from app.modules.invoice.models import Invoice
from app.modules.membership.models import Membership
from app.modules.products.models import Product
from app.modules.search.service import LIMIT_PER_TYPE
from app.modules.user.models import User
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.invoice import InvoiceStatus
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

TODAY = date.today()


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

    def user(tag):
        u = User(first_name=tag, last_name="X", email=f"{tag}-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
        db.add(u)
        return u

    w.owner, w.employee, w.viewer = user("owner"), user("emp"), user("view")
    db.flush()
    w.biz = Business(name="Arama", slug=f"ara-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    db.add_all([
        Membership(user_id=w.owner.id, business_id=w.biz.id, role=MembershipRole.OWNER),
        Membership(user_id=w.employee.id, business_id=w.biz.id, role=MembershipRole.EMPLOYEE),
        Membership(user_id=w.viewer.id, business_id=w.biz.id, role=MembershipRole.VIEWER),
    ])

    db.add(Customer(business_id=w.biz.id, name="Ayşe Yılmaz", phone="0555 123 45 67", email="ayse@example.com"))
    db.add(Customer(business_id=w.biz.id, name="IŞIK Kaya", phone="0532 000 11 22"))
    for i in range(8):
        db.add(Customer(business_id=w.biz.id, name=f"Mehmet Demir {i}"))

    def appt(days, name="Ayşe Yılmaz", hour=10):
        db.add(Appointment(business_id=w.biz.id, customer_name=name, customer_phone="0555 123 45 67",
                           appointment_date=TODAY + timedelta(days=days), start_time=time(hour),
                           status=AppointmentStatus.CONFIRMED))

    for days in (-30, -2, 5, 1, 12):
        appt(days)

    db.add(Invoice(business_id=w.biz.id, customer_name="Ayşe Yılmaz", invoice_number=f"FT-{sfx}-001", items=[],
                   subtotal=Decimal(1250), tax_rate=0, tax_amount=0, total_amount=Decimal(1250),
                   status=InvoiceStatus.PAID))
    db.add(Product(business_id=w.biz.id, name="Şampuan Işıltı", sku="SMP-001", barcode="8690000000011", current_stock=7))
    db.commit()
    return w


def search(client, w, q, user=None):
    return client.get(f"{API}/businesses/{w.biz.id}/search", params={"q": q}, headers=auth(user or w.owner))


def test_finds_every_type_with_turkish_folding(client, db):
    w = make_world(db)
    body = search(client, w, "ayse").json()
    assert [c["name"] for c in body["customers"]["items"]] == ["Ayşe Yılmaz"]
    assert body["appointments"]["total"] == 5
    assert body["invoices"]["items"][0]["customer_name"] == "Ayşe Yılmaz"
    assert body["products"]["total"] == 0

    assert [c["name"] for c in search(client, w, "ışık").json()["customers"]["items"]] == ["IŞIK Kaya"]
    assert [p["name"] for p in search(client, w, "SAMPUAN").json()["products"]["items"]] == ["Şampuan Işıltı"]


def test_phone_sku_barcode_and_invoice_number(client, db):
    w = make_world(db)
    assert search(client, w, "555 123").json()["customers"]["items"][0]["name"] == "Ayşe Yılmaz"
    assert search(client, w, "smp-001").json()["products"]["items"][0]["current_stock"] == 7
    assert search(client, w, "86900000").json()["products"]["total"] == 1
    assert search(client, w, "-001").json()["invoices"]["total"] == 1


def test_each_type_is_capped_but_reports_its_total(client, db):
    w = make_world(db)
    group = search(client, w, "mehmet").json()["customers"]
    assert group["total"] == 8
    assert len(group["items"]) == LIMIT_PER_TYPE


def test_appointments_upcoming_soonest_first_then_most_recent_past(client, db):
    w = make_world(db)
    items = search(client, w, "ayse").json()["appointments"]["items"]
    dates = [date.fromisoformat(a["appointment_date"]) for a in items]
    offsets = [(d - TODAY).days for d in dates]
    assert offsets == [1, 5, 12, -2, -30]


@pytest.mark.parametrize("role", ["employee", "viewer"])
def test_invoice_amounts_hidden_from_roles_without_finance_access(client, db, role):
    w = make_world(db)
    hit = search(client, w, "ayse", user=getattr(w, role)).json()["invoices"]["items"][0]
    assert hit["total_amount"] is None
    assert hit["invoice_number"].endswith("-001")
    assert search(client, w, "ayse").json()["invoices"]["items"][0]["total_amount"] == 1250.0


def test_other_business_and_short_queries_are_rejected(client, db):
    w = make_world(db)
    other = make_world(db)
    assert search(client, w, "ayse", user=other.owner).status_code in (403, 404)
    assert search(client, w, "a").status_code == 422


def test_results_never_leak_across_businesses(client, db):
    w = make_world(db)
    make_world(db)  # a second business with the same names
    body = search(client, w, "ayse").json()
    assert body["customers"]["total"] == 1
    assert body["appointments"]["total"] == 5
