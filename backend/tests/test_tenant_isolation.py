"""
Multi-tenant isolation tests.

These run against a real PostgreSQL database (membership checks are SQL
queries, so a mocked session cannot prove isolation). The database is taken
from TEST_DATABASE_URL, or defaults to "<POSTGRES_DB>_test" on the server in
.env. When no database is reachable the whole module is skipped, so the
regular mocked test suite keeps working without Docker.

    # PowerShell, with docker compose running:
    pytest tests/test_tenant_isolation.py
"""
import uuid
from datetime import date, datetime, UTC

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.main import app
from app.modules.business.models import Business
from app.modules.cash_register.models import CashRegister
from app.modules.customers.models import Customer
from app.modules.invoice.models import Invoice
from app.modules.membership.models import Membership
from app.modules.notifications.models import Notification
from app.modules.user.models import User
from app.shared.enums.cash_register import CashRegisterStatus
from app.shared.enums.invoice import InvoiceStatus
from app.shared.enums.membership import MembershipRole
from app.shared.enums.notification import NotificationType
from app.shared.enums.user import UserStatus
from app.shared.security import business as business_security
from tests.pg_support import API, auth, make_client, make_engine, release_client


# ------------------------------------------------------------------ database

@pytest.fixture(scope="module")
def engine():
    eng = make_engine()
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture(scope="module")
def client(engine):
    with make_client(engine) as c:
        yield c
    release_client()


# ------------------------------------------------------------------ data

class World:
    """Two businesses (A, B) with owners and a few records in B."""


@pytest.fixture(scope="module")
def world(engine):
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    w = World()
    sfx = uuid.uuid4().hex[:8]

    def user(name):
        u = User(first_name=name, last_name="Test", email=f"{name}-{sfx}@test.local",
                 password_hash="x", status=UserStatus.ACTIVE)
        db.add(u)
        db.flush()
        return u

    def business(name):
        b = Business(name=name, slug=f"{name.lower()}-{sfx}", industry="beauty",
                     email=f"{name.lower()}-{sfx}@test.local", phone="000")
        db.add(b)
        db.flush()
        return b

    w.owner_a, w.owner_b = user("ownera"), user("ownerb")
    w.admin_a, w.viewer_a, w.employee_b = user("admina"), user("viewera"), user("employeeb")
    w.a, w.b = business("Alpha"), business("Beta")
    db.add_all([
        Membership(user_id=w.owner_a.id, business_id=w.a.id, role=MembershipRole.OWNER),
        Membership(user_id=w.admin_a.id, business_id=w.a.id, role=MembershipRole.ADMIN),
        Membership(user_id=w.viewer_a.id, business_id=w.a.id, role=MembershipRole.VIEWER),
        Membership(user_id=w.owner_b.id, business_id=w.b.id, role=MembershipRole.OWNER),
        Membership(user_id=w.employee_b.id, business_id=w.b.id, role=MembershipRole.EMPLOYEE),
    ])

    w.customer_b = Customer(business_id=w.b.id, name="B Customer", phone="555")
    w.invoice_b = Invoice(business_id=w.b.id, customer_name="B Customer", invoice_number=f"B-{sfx}",
                          items=[], subtotal=100, tax_rate=0, tax_amount=0, total_amount=100,
                          status=InvoiceStatus.DRAFT)
    w.notification_b = Notification(business_id=w.b.id, user_id=w.owner_b.id, title="t", message="m",
                                    type=NotificationType.SYSTEM)
    w.register_b = CashRegister(business_id=w.b.id, register_date=date.today(), opening_balance=0,
                                status=CashRegisterStatus.OPEN, opened_at=datetime.now(UTC))
    # A notification in A addressed to the owner, used to check per-user scoping inside a business.
    w.notification_a_owner = Notification(business_id=w.a.id, user_id=w.owner_a.id, title="t", message="m",
                                          type=NotificationType.SYSTEM)
    db.add_all([w.customer_b, w.invoice_b, w.notification_b, w.register_b, w.notification_a_owner])
    db.commit()
    w.db = db
    yield w
    db.close()


# ------------------------------------------------------------------ 1. cross-business access is 403

# One or more representative endpoints for every router that was unprotected.
READ_ENDPOINTS = [
    "/customers",
    "/services",
    "/appointments",
    "/appointments/available-slots?date=2026-10-05",
    "/invoices",
    "/invoices/stats",
    "/notifications",
    "/cash-register",
    "/schedule-blocks",
    "/reminders/configs",
    "/customer-tags",
    "/loyalty/wallets",
    "/surveys",
    "/reviews",
    "/expense-categories",
    "/expenses",
    "/branches",
    "/staff",
    "/products",
    "/product-sales",
    "/packages",
    "/customer-packages",
    "/installments",
    "/reports/dashboard-stats",
    "/chat/sessions",
    "/business-hours",
]


@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_member_of_a_cannot_read_business_b(client, world, path):
    r = client.get(f"{API}/businesses/{world.b.id}{path}", headers=auth(world.owner_a))
    assert r.status_code == 403, r.text


@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_member_of_b_can_read_business_b(client, world, path):
    r = client.get(f"{API}/businesses/{world.b.id}{path}", headers=auth(world.employee_b))
    assert r.status_code not in (401, 403), r.text


def test_member_of_a_cannot_write_into_business_b(client, world):
    r = client.post(f"{API}/businesses/{world.b.id}/customers",
                    json={"name": "Injected", "phone": "123"}, headers=auth(world.owner_a))
    assert r.status_code == 403
    world.db.expire_all()
    assert world.db.query(Customer).filter_by(business_id=world.b.id, name="Injected").count() == 0


def test_member_of_a_cannot_delete_in_business_b(client, world):
    r = client.delete(f"{API}/businesses/{world.b.id}/customers/{world.customer_b.id}", headers=auth(world.owner_a))
    assert r.status_code == 403
    world.db.expire_all()
    assert world.db.get(Customer, world.customer_b.id).is_deleted is False


def test_unknown_business_is_403(client, world):
    r = client.get(f"{API}/businesses/{uuid.uuid4()}/customers", headers=auth(world.owner_a))
    assert r.status_code == 403


def test_missing_token_is_401(client, world):
    r = client.get(f"{API}/businesses/{world.b.id}/customers")
    assert r.status_code == 401


# ------------------------------------------------------------------ 2. ID-based leaks inside own business path are 404

def test_invoice_of_b_not_readable_through_a(client, world):
    r = client.get(f"{API}/businesses/{world.a.id}/invoices/{world.invoice_b.id}", headers=auth(world.owner_a))
    assert r.status_code == 404


def test_invoice_of_b_not_modifiable_through_a(client, world):
    base = f"{API}/businesses/{world.a.id}/invoices/{world.invoice_b.id}"
    h = auth(world.owner_a)
    assert client.patch(base, json={"customer_name": "hacked"}, headers=h).status_code == 404
    assert client.post(f"{base}/pay?payment_method=CASH", headers=h).status_code == 404
    assert client.post(f"{base}/cancel", headers=h).status_code == 404
    world.db.expire_all()
    inv = world.db.get(Invoice, world.invoice_b.id)
    assert inv.status == InvoiceStatus.DRAFT and inv.customer_name == "B Customer"


def test_invoice_still_reachable_by_its_owner(client, world):
    r = client.get(f"{API}/businesses/{world.b.id}/invoices/{world.invoice_b.id}", headers=auth(world.owner_b))
    assert r.status_code == 200


def test_notification_of_b_not_markable_through_a(client, world):
    r = client.post(f"{API}/businesses/{world.a.id}/notifications/{world.notification_b.id}/read",
                    headers=auth(world.owner_a))
    assert r.status_code == 404
    world.db.expire_all()
    assert world.db.get(Notification, world.notification_b.id).is_read is False


def test_notification_of_another_user_in_same_business_not_markable(client, world):
    r = client.post(f"{API}/businesses/{world.a.id}/notifications/{world.notification_a_owner.id}/read",
                    headers=auth(world.admin_a))
    assert r.status_code == 404
    r = client.post(f"{API}/businesses/{world.a.id}/notifications/{world.notification_a_owner.id}/read",
                    headers=auth(world.owner_a))
    assert r.status_code == 200


def test_cash_register_of_b_not_accessible_through_a(client, world):
    base = f"{API}/businesses/{world.a.id}/cash-register/{world.register_b.id}"
    h = auth(world.owner_a)
    assert client.get(base, headers=h).status_code == 404
    assert client.get(f"{base}/summary", headers=h).status_code == 404
    assert client.post(f"{base}/close", json={"closing_balance": 0}, headers=h).status_code == 404
    assert client.post(f"{base}/transactions", json={"transaction_type": "DEPOSIT", "amount": 10},
                       headers=h).status_code == 404
    world.db.expire_all()
    assert world.db.get(CashRegister, world.register_b.id).status == CashRegisterStatus.OPEN


def test_cash_register_still_reachable_by_its_owner(client, world):
    base = f"{API}/businesses/{world.b.id}/cash-register/{world.register_b.id}"
    assert client.get(base, headers=auth(world.owner_b)).status_code == 200
    assert client.get(f"{base}/summary", headers=auth(world.owner_b)).status_code == 200


# ------------------------------------------------------------------ 3. RAG: business comes only from the path

class _FakeRAG:
    calls: list = []

    def ask(self, business_id, user_id, question, top_k):
        _FakeRAG.calls.append(business_id)
        from types import SimpleNamespace
        return SimpleNamespace(answer="ok", sources=[], retrieved_chunks=[])


@pytest.fixture
def fake_rag(monkeypatch):
    _FakeRAG.calls = []
    monkeypatch.setattr("app.modules.rag.router.get_rag_service", lambda db: _FakeRAG())
    return _FakeRAG


def test_rag_ignores_business_id_in_body(client, world, fake_rag):
    r = client.post(f"{API}/businesses/{world.a.id}/rag/ask",
                    json={"business_id": str(world.b.id), "question": "fiyatlar?"},
                    headers=auth(world.owner_a))
    assert r.status_code == 200, r.text
    assert fake_rag.calls == [world.a.id]


def test_rag_works_without_business_id_in_body(client, world, fake_rag):
    r = client.post(f"{API}/businesses/{world.a.id}/rag/ask", json={"question": "fiyatlar?"},
                    headers=auth(world.owner_a))
    assert r.status_code == 200
    assert fake_rag.calls == [world.a.id]


def test_rag_on_other_business_is_403(client, world, fake_rag):
    r = client.post(f"{API}/businesses/{world.b.id}/rag/ask", json={"question": "x"}, headers=auth(world.owner_a))
    assert r.status_code == 403
    assert fake_rag.calls == []


def test_old_unscoped_rag_route_is_gone(client, world):
    r = client.post(f"{API}/rag/ask", json={"business_id": str(world.b.id), "question": "x"},
                    headers=auth(world.owner_a))
    assert r.status_code == 404


# ------------------------------------------------------------------ 4. role checks share the same membership lookup

def test_viewer_cannot_change_business_hours_but_admin_can(client, world):
    week = {"items": [{"day_of_week": 0, "open_time": "09:00:00", "close_time": "17:00:00"}]}
    url = f"{API}/businesses/{world.a.id}/business-hours"
    assert client.put(url, json=week, headers=auth(world.viewer_a)).status_code == 403
    assert client.put(url, json=week, headers=auth(world.admin_a)).status_code == 200


def test_invitations_require_owner(client, world):
    url = f"{API}/businesses/{world.a.id}/invitations"
    assert client.get(url, headers=auth(world.admin_a)).status_code == 403
    assert client.get(url, headers=auth(world.owner_a)).status_code == 200


@pytest.fixture
def role_probe_app(client):
    """Tiny app exercising require_admin / require_owner / require_business_member directly."""
    probe = FastAPI()

    @probe.get("/b/{business_id}/admin")
    def _admin(user=Depends(business_security.require_admin)):
        return {"ok": True}

    @probe.get("/b/{business_id}/owner")
    def _owner(user=Depends(business_security.require_owner)):
        return {"ok": True}

    @probe.get("/b/{business_id}/member")
    def _member(user=Depends(business_security.require_business_member)):
        return {"ok": True}

    probe.dependency_overrides = app.dependency_overrides
    return TestClient(probe)


@pytest.mark.parametrize("who,admin,owner,member", [
    ("owner_a", 200, 200, 200),
    ("admin_a", 200, 403, 200),
    ("viewer_a", 403, 403, 200),
    ("owner_b", 403, 403, 403),
])
def test_require_admin_owner_member(role_probe_app, world, who, admin, owner, member):
    h = auth(getattr(world, who))
    assert role_probe_app.get(f"/b/{world.a.id}/admin", headers=h).status_code == admin
    assert role_probe_app.get(f"/b/{world.a.id}/owner", headers=h).status_code == owner
    assert role_probe_app.get(f"/b/{world.a.id}/member", headers=h).status_code == member
