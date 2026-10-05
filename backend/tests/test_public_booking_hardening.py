"""
Online booking hardening: public data, validation, "farkı yok" assignment,
auto-confirm setting, concurrency lock, spam limits and notifications.
PostgreSQL integration tests; skipped when the database is unreachable.
"""
import threading
import uuid
from datetime import date, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.appointments.models import Appointment
from app.modules.branches.models import Branch
from app.modules.business.models import Business
from app.modules.business_hours.models import BusinessHours
from app.modules.customers.models import Customer
from app.modules.membership.models import Membership
from app.modules.notifications.models import Notification
from app.modules.public_booking.schemas import PublicBookingCreate, normalize_phone
from app.modules.services.models import Service
from app.modules.staff.models import StaffProfile, StaffService
from app.modules.user.models import User
from app.shared.enums.business import BusinessStatus
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from app.shared.security.rate_limit import RateLimiter, limiter
from app.shared.utils.slug import generate_slug
from tests.pg_support import API, auth, make_engine

TOMORROW = date.today() + timedelta(days=1)


# ====================================================================== unit

@pytest.mark.parametrize("raw, expected", [
    ("0532 123 45 67", "05321234567"),
    ("+90 (532) 123-45-67", "05321234567"),
    ("5321234567", "05321234567"),
    ("0212 555 66 77", "02125556677"),
])
def test_phone_normalisation(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["1", "12345", "abc", "0532 123", "0932 123 45 67", "05321234567890"])
def test_invalid_phones(raw):
    with pytest.raises(ValueError):
        normalize_phone(raw)


def test_booking_payload_cleans_name_and_email():
    data = PublicBookingCreate(customer_name="  Ayşe   Kaya ", customer_phone="0532 123 45 67",
                               customer_email=" Ayse@Example.COM ", service_id=uuid.uuid4(),
                               date=TOMORROW, start_time=time(10))
    assert data.customer_name == "Ayşe Kaya"
    assert data.customer_email == "ayse@example.com"
    for bad in ("1", "  ", "12345"):
        with pytest.raises(ValueError):
            PublicBookingCreate(customer_name=bad, customer_phone="05321234567", service_id=uuid.uuid4(),
                                date=TOMORROW, start_time=time(10))


def test_turkish_slug():
    assert generate_slug("Güzellik Salonu") == "guzellik-salonu"
    assert generate_slug("Çiçek Kuaför & Spa") == "cicek-kuafor-spa"
    assert generate_slug("IŞIK Berber") == "isik-berber"


def test_rate_limiter_falls_back_to_memory_when_redis_is_down():
    rl = RateLimiter("redis://127.0.0.1:1/0")  # nothing listens there
    assert [rl.hit("b", "1.2.3.4", 2, 60) for _ in range(3)] == [True, True, False]
    assert rl.hit("b", "5.6.7.8", 2, 60)  # other IPs are independent


# ====================================================================== fixtures

@pytest.fixture(scope="module")
def engine():
    eng = make_engine()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture(scope="module")
def Session(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="module")
def client(Session):
    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def mail(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_BOOKING_LIMIT", 1000)
    monkeypatch.setattr(settings, "PUBLIC_QUERY_LIMIT", 1000)
    monkeypatch.setattr(settings, "MAIL_FROM", "no-reply@test.local")
    monkeypatch.setattr(limiter, "redis_url", None)
    limiter.reset()
    sent = []
    monkeypatch.setattr("app.modules.public_booking.notify.SMTPClient.send", lambda **kw: sent.append(kw))
    return sent


class World:
    pass


@pytest.fixture
def w(Session):
    db = Session()
    sfx = uuid.uuid4().hex[:8]
    w = World()
    w.db = db

    def user(name):
        u = User(first_name=name, last_name="T", email=f"{name}-{sfx}@t.local", password_hash="x", status=UserStatus.ACTIVE)
        db.add(u)
        db.flush()
        return u

    w.biz = Business(name="Kuaför", slug=f"kuafor-{sfx}", industry="beauty", email=f"k-{sfx}@example.com", phone="02121112233")
    w.other = Business(name="Rakip", slug=f"rakip-{sfx}", industry="beauty", email=f"r-{sfx}@example.com", phone="0")
    db.add_all([w.biz, w.other])
    db.flush()
    w.owner, w.admin, w.employee = user("owner"), user("admin"), user("employee")
    db.add_all([
        Membership(user_id=w.owner.id, business_id=w.biz.id, role=MembershipRole.OWNER),
        Membership(user_id=w.admin.id, business_id=w.biz.id, role=MembershipRole.ADMIN),
        Membership(user_id=w.employee.id, business_id=w.biz.id, role=MembershipRole.EMPLOYEE),
    ])
    w.main = Branch(business_id=w.biz.id, name="Merkez", address="Moda Cad. 12 Kadıköy", is_main=True)
    w.closed_branch = Branch(business_id=w.biz.id, name="Kapalı Şube", is_active=False)
    w.cut = Service(business_id=w.biz.id, name="Saç Kesimi", price=350, duration_minutes=60)
    w.nails = Service(business_id=w.biz.id, name="Manikür", price=200, duration_minutes=30)
    w.rival_service = Service(business_id=w.other.id, name="Rakip Hizmet", price=1, duration_minutes=30)
    db.add_all([w.main, w.closed_branch, w.cut, w.nails, w.rival_service])
    db.flush()
    w.elif_ = StaffProfile(business_id=w.biz.id, full_name="Elif Usta", title="Kuaför", phone="05329998877",
                           email="elif@private.test")
    w.mert = StaffProfile(business_id=w.biz.id, full_name="Mert Usta", phone="05320001122", email="mert@private.test")
    w.rival_staff = StaffProfile(business_id=w.other.id, full_name="Rakip Usta", phone="05321110000")
    db.add_all([w.elif_, w.mert, w.rival_staff])
    db.flush()
    db.add_all([
        StaffService(staff_id=w.elif_.id, service_id=w.cut.id),
        StaffService(staff_id=w.mert.id, service_id=w.cut.id),
        StaffService(staff_id=w.rival_staff.id, service_id=w.rival_service.id),
        # nails: nobody assigned -> business-wide calendar
    ])
    db.commit()
    yield w
    db.close()


def url(w, path, slug=None):
    return f"{API}/public/booking/{slug or w.biz.slug}/{path}"


def book(client, w, **overrides):
    body = {"customer_name": "Ali Veli", "customer_phone": "0555 123 45 67", "customer_email": "ali@example.com",
            "service_id": str(w.cut.id), "date": TOMORROW.isoformat(), "start_time": "10:00"}
    body.update({k: (str(v) if isinstance(v, uuid.UUID) else v) for k, v in overrides.items()})
    return client.post(url(w, "book"), json=body)


def appts(w):
    w.db.expire_all()
    return w.db.scalars(select(Appointment).where(Appointment.business_id == w.biz.id)).all()


# ====================================================================== part 1: public data

def test_staff_endpoint_exposes_display_data_only(client, w):
    r = client.get(url(w, "staff"), params={"service_id": str(w.cut.id)})
    assert r.status_code == 200
    rows = r.json()
    assert {s["full_name"] for s in rows} == {"Elif Usta", "Mert Usta"}
    for row in rows:
        assert set(row) == {"id", "full_name", "title", "bio", "avatar_url", "branch_id", "services"}
    assert "private.test" not in r.text and "0532999" not in r.text


def test_staff_of_another_business_never_shows(client, w):
    r = client.get(url(w, "staff"), params={"service_id": str(w.rival_service.id)})
    assert r.status_code == 200 and r.json() == []


def test_info_has_contact_address_and_hours(client, w):
    w.db.add_all([BusinessHours(business_id=w.biz.id, day_of_week=d, open_time=time(10), close_time=time(20))
                  for d in range(6)] + [BusinessHours(business_id=w.biz.id, day_of_week=6, is_closed=True)])
    w.db.commit()
    info = client.get(url(w, "info")).json()
    assert info["phone"] == "02121112233"
    assert info["address"] == "Moda Cad. 12 Kadıköy"
    assert info["opening_hours"][0] == {"day_of_week": 0, "open_time": "10:00:00", "close_time": "20:00:00", "is_closed": False}
    assert info["opening_hours"][6]["is_closed"] is True
    assert "email" not in info


def test_default_hours_when_not_configured(client, w):
    hours = client.get(url(w, "info")).json()["opening_hours"]
    assert len(hours) == 7 and all(h["open_time"] == "09:00:00" for h in hours)


def test_inactive_branch_hidden_and_rejected(client, w):
    names = [b["name"] for b in client.get(url(w, "branches")).json()]
    assert names == ["Merkez"]
    assert book(client, w, branch_id=w.closed_branch.id).status_code == 404


@pytest.mark.parametrize("status", [BusinessStatus.SUSPENDED, BusinessStatus.INACTIVE])
def test_suspended_business_is_not_public(client, w, status):
    w.biz.status = status
    w.db.commit()
    assert client.get(url(w, "info")).status_code == 404
    assert book(client, w).status_code == 404


def test_staff_must_offer_the_service(client, w):
    r = book(client, w, service_id=w.nails.id, staff_id=w.elif_.id)
    assert r.status_code == 404 and "bu hizmeti vermiyor" in r.json()["message"]
    r = client.get(url(w, "available-slots"), params={"date": TOMORROW.isoformat(), "service_id": str(w.nails.id),
                                                      "staff_id": str(w.elif_.id)})
    assert r.status_code == 404


@pytest.mark.parametrize("field, value", [("customer_phone", "1"), ("customer_phone", "abc"), ("customer_name", "1"),
                                          ("customer_email", "not-an-email")])
def test_invalid_contact_details_are_rejected(client, w, field, value):
    r = book(client, w, **{field: value})
    assert r.status_code == 422
    assert appts(w) == []


def test_honeypot_blocks_bots(client, w):
    r = book(client, w, website="http://spam.example")
    assert r.status_code == 400
    assert appts(w) == []


def test_slug_collision_gets_suffix(client, w):
    sfx = uuid.uuid4().hex[:6]
    name = f"Güzellik Salonu {sfx}"
    headers = auth(w.owner)
    body = {"name": name, "industry": "beauty", "phone": "02120000000"}
    r1 = client.post(f"{API}/businesses", json={**body, "email": f"a{sfx}@example.com"}, headers=headers)
    r2 = client.post(f"{API}/businesses", json={**body, "email": f"b{sfx}@example.com"}, headers=headers)
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text
    assert r1.json()["slug"] == f"guzellik-salonu-{sfx}"
    assert r2.json()["slug"] == f"guzellik-salonu-{sfx}-2"


def test_slug_of_deleted_business_is_not_reused(client, w):
    sfx = uuid.uuid4().hex[:6]
    w.db.add(Business(name="x", slug=f"silinmis-{sfx}", industry="b", email=f"s{sfx}@t.local", phone="0", is_deleted=True))
    w.db.commit()
    r = client.post(f"{API}/businesses", json={"name": f"Silinmiş {sfx}", "industry": "beauty", "phone": "02120000000",
                                               "email": f"n{sfx}@example.com"}, headers=auth(w.owner))
    assert r.status_code == 201, r.text
    assert r.json()["slug"] == f"silinmis-{sfx}-2"


# ====================================================================== part 2: assignment, auto-confirm, lock

def test_any_staff_assigns_least_busy_then_fills_up(client, w):
    w.db.add(Appointment(business_id=w.biz.id, customer_name="X", staff_id=w.elif_.id, service_id=w.cut.id,
                         appointment_date=TOMORROW, start_time=time(15), end_time=time(16)))
    w.db.commit()
    first = book(client, w)
    assert first.status_code == 201, first.text
    assert first.json()["staff_name"] == "Mert Usta"  # Elif already has one appointment that day
    second = book(client, w, customer_phone="05550000002")
    assert second.json()["staff_name"] == "Elif Usta"
    third = book(client, w, customer_phone="05550000003")
    assert third.status_code == 409
    slots = client.get(url(w, "available-slots"), params={"date": TOMORROW.isoformat(), "service_id": str(w.cut.id)}).json()
    assert "10:00:00" not in slots["available_slots"] and "11:00:00" in slots["available_slots"]


def test_chosen_staff_busy_but_other_free(client, w):
    assert book(client, w, staff_id=w.elif_.id).status_code == 201
    assert book(client, w, staff_id=w.elif_.id, customer_phone="05550000002").status_code == 409
    r = book(client, w, staff_id=w.mert.id, customer_phone="05550000003")
    assert r.status_code == 201 and r.json()["staff_name"] == "Mert Usta"


def test_service_without_staff_uses_business_calendar(client, w):
    r = book(client, w, service_id=w.nails.id)
    assert r.status_code == 201 and r.json()["staff_id"] is None
    assert book(client, w, service_id=w.nails.id, customer_phone="05550000002").status_code == 409


def test_default_status_pending_and_auto_confirm_setting(client, w):
    assert book(client, w).json()["status"] == "PENDING"
    r = client.patch(f"{API}/businesses/{w.biz.id}", json={"online_booking_auto_confirm": True}, headers=auth(w.owner))
    assert r.status_code == 200 and r.json()["online_booking_auto_confirm"] is True
    assert book(client, w, start_time="12:00", customer_phone="05550000002").json()["status"] == "CONFIRMED"


def test_employee_cannot_change_auto_confirm(client, w):
    r = client.patch(f"{API}/businesses/{w.biz.id}", json={"online_booking_auto_confirm": True}, headers=auth(w.employee))
    assert r.status_code == 403


def test_parallel_bookings_for_the_same_slot_create_exactly_one(Session, w):
    from app.modules.public_booking.router import get_service

    results, errors = [], []
    barrier = threading.Barrier(6)

    def attempt(i):
        db = Session()
        try:
            service = get_service(db)
            data = PublicBookingCreate(customer_name=f"Kişi {i}", customer_phone=f"0555000001{i}",
                                       service_id=w.nails.id, date=TOMORROW, start_time=time(10))
            barrier.wait()
            results.append(service.create_public_booking(w.biz.slug, data))
        except Exception as exc:  # 409 expected for all but one
            errors.append(type(exc).__name__)
        finally:
            db.close()

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 1
    assert errors == ["ConflictException"] * 5
    assert len(appts(w)) == 1
    # losers left no orphan customers behind (single transaction)
    names = w.db.scalars(select(Customer.name).where(Customer.business_id == w.biz.id)).all()
    assert len(names) == 1


# ====================================================================== part 3: spam limits

def test_ip_rate_limit_returns_429(client, w, monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_BOOKING_LIMIT", 2)
    assert book(client, w).status_code == 201
    assert book(client, w, start_time="12:00", customer_phone="05550000002").status_code == 201
    r = book(client, w, start_time="14:00", customer_phone="05550000003")
    assert r.status_code == 429
    assert "Çok fazla istek" in r.json()["message"]
    assert r.headers["retry-after"] == str(settings.PUBLIC_BOOKING_WINDOW_SECONDS)
    assert len(appts(w)) == 2


def test_query_rate_limit(client, w, monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_QUERY_LIMIT", 3)
    codes = [client.get(url(w, "services")).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]


def test_open_bookings_per_phone_are_capped(client, w):
    for hour in ("09:00", "11:00", "13:00"):
        assert book(client, w, start_time=hour).status_code == 201
    r = book(client, w, start_time="15:00", customer_phone="+90 555 123 45 67")  # same number, other format
    assert r.status_code == 409 and "çok fazla randevu" in r.json()["message"]
    assert book(client, w, start_time="15:00", customer_phone="05559998877").status_code == 201


# ====================================================================== part 4: notifications

def test_owner_and_admin_get_a_bell_notification(client, w):
    r = book(client, w)
    assert r.status_code == 201
    w.db.expire_all()
    notes = w.db.scalars(select(Notification).where(Notification.business_id == w.biz.id)).all()
    assert {n.user_id for n in notes} == {w.owner.id, w.admin.id}
    note = notes[0]
    assert note.title == "Yeni online randevu"
    assert "Ali Veli" in note.message and "Saç Kesimi" in note.message and "Onayınızı bekliyor" in note.message
    assert str(note.reference_id) == r.json()["id"]


def test_customer_gets_confirmation_email(client, w, mail):
    assert book(client, w).status_code == 201
    [m] = mail
    assert m["to_email"] == "ali@example.com"
    assert m["subject"] == "Randevu talebiniz alındı – Kuaför"
    assert "Saç Kesimi" in m["text"] and "Ali Veli" in m["text"]


def test_auto_confirmed_email_wording(client, w, mail):
    w.biz.online_booking_auto_confirm = True
    w.db.commit()
    assert book(client, w).status_code == 201
    assert mail[0]["subject"] == "Randevunuz onaylandı – Kuaför"


def test_no_email_without_address_and_smtp_failure_does_not_break_booking(client, w, mail, monkeypatch):
    assert book(client, w, customer_email=None).status_code == 201
    assert mail == []

    def boom(**kw):
        raise OSError("smtp down")

    monkeypatch.setattr("app.modules.public_booking.notify.SMTPClient.send", boom)
    assert book(client, w, start_time="12:00", customer_phone="05550000002").status_code == 201


def test_non_ascii_email_is_rejected_with_turkish_message():
    with pytest.raises(ValueError) as exc:
        PublicBookingCreate(customer_name="Ayşe Kaya", customer_phone="05321112233", customer_email="ayşe@example.com",
                            service_id=uuid.uuid4(), date=date.today(), start_time=time(10, 0))
    assert "Türkçe karakter" in str(exc.value)
