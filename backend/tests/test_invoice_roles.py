"""
Invoices by role: every member reads invoices, only owner/admin see amounts and
may create, edit, pay or cancel. Same rule as reports, insights and global search.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.agent_actions.models import AgentAction
from app.modules.appointments.models import Appointment
from app.modules.business.models import Business
from app.modules.invoice.models import Invoice
from app.modules.membership.models import Membership
from app.modules.user.models import User
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.invoice import InvoiceStatus, PaymentMethod
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

FINANCE = ["owner", "admin"]
OTHERS = ["employee", "viewer"]
ALL = FINANCE + OTHERS


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
    w.biz = Business(name="Rol", slug=f"rol-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    roles = {"owner": MembershipRole.OWNER, "admin": MembershipRole.ADMIN,
             "employee": MembershipRole.EMPLOYEE, "viewer": MembershipRole.VIEWER}
    for name, role in roles.items():
        u = User(first_name=name, last_name="X", email=f"{name}-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
        db.add(u)
        db.flush()
        db.add(Membership(user_id=u.id, business_id=w.biz.id, role=role))
        setattr(w, name, u)
    w.invoice = Invoice(
        business_id=w.biz.id, customer_name="Ayşe Yılmaz", invoice_number=f"FT-{sfx}", status=InvoiceStatus.PAID,
        items=[{"description": "Saç kesimi", "quantity": 2, "unit_price": 500.0, "total": 1000.0}],
        subtotal=Decimal(1000), tax_rate=20, tax_amount=Decimal(200), total_amount=Decimal(1200),
        payment_method=PaymentMethod.CASH, paid_at=datetime.now(UTC),
    )
    w.draft = Invoice(business_id=w.biz.id, customer_name="Mehmet", invoice_number=f"FT-{sfx}-2", items=[],
                      subtotal=Decimal(10), tax_rate=0, tax_amount=Decimal(0), total_amount=Decimal(10),
                      status=InvoiceStatus.DRAFT)
    w.appt = Appointment(business_id=w.biz.id, customer_name="Ayşe Yılmaz", appointment_date=datetime.now().date(),
                         start_time=time(10), status=AppointmentStatus.COMPLETED)
    db.add_all([w.invoice, w.draft, w.appt])
    now = datetime.now(UTC)
    w.invoice_draft = AgentAction(business_id=w.biz.id, requested_by=w.owner.id, action_type="CREATE_INVOICE",
                                  status="PENDING", payload={"total_amount": 999}, created_at=now)
    w.expense_draft = AgentAction(business_id=w.biz.id, requested_by=w.owner.id, action_type="CREATE_EXPENSE",
                                  status="PENDING", payload={"amount": 50}, created_at=now - timedelta(minutes=1))
    w.campaign = AgentAction(business_id=w.biz.id, requested_by=w.owner.id, action_type="CREATE_CAMPAIGN",
                             status="PENDING", payload={"title": "Kampanya"}, created_at=now - timedelta(minutes=2))
    db.add_all([w.invoice_draft, w.expense_draft, w.campaign])
    db.commit()
    return w


def url(w, path=""):
    return f"{API}/businesses/{w.biz.id}/invoices{path}"


def as_(w, role):
    return auth(getattr(w, role))


# ---------------------------------------------------------------- reading

@pytest.mark.parametrize("role", FINANCE)
def test_finance_roles_see_amounts(client, w, role):
    inv = next(i for i in client.get(url(w), headers=as_(w, role)).json() if i["id"] == str(w.invoice.id))
    assert inv["total_amount"] == 1200.0 and inv["subtotal"] == 1000.0 and inv["tax_amount"] == 200.0
    assert inv["items"][0]["unit_price"] == 500.0
    assert client.get(url(w, "/stats"), headers=as_(w, role)).json()["total_revenue"] == 1200.0


@pytest.mark.parametrize("role", OTHERS)
def test_other_roles_see_invoices_without_amounts(client, w, role):
    res = client.get(url(w), headers=as_(w, role))
    assert res.status_code == 200
    assert res.headers["X-Total-Count"] == "2"
    inv = next(i for i in res.json() if i["id"] == str(w.invoice.id))
    # money hidden
    assert inv["subtotal"] is None and inv["tax_amount"] is None and inv["total_amount"] is None
    assert inv["items"] == [{"description": "Saç kesimi", "quantity": 2, "unit_price": None, "total": None}]
    # everything else visible
    assert inv["invoice_number"] == w.invoice.invoice_number
    assert inv["customer_name"] == "Ayşe Yılmaz" and inv["status"] == "PAID"
    assert inv["tax_rate"] == 20.0 and inv["payment_method"] == "CASH" and inv["paid_at"]


@pytest.mark.parametrize("role", OTHERS)
def test_other_roles_detail_and_stats(client, w, role):
    inv = client.get(url(w, f"/{w.invoice.id}"), headers=as_(w, role)).json()
    assert inv["total_amount"] is None and inv["items"][0]["total"] is None
    stats = client.get(url(w, "/stats"), headers=as_(w, role)).json()
    assert stats == {"total_revenue": None, "paid_count": 1, "pending_count": 1, "overdue_count": 0}


# ---------------------------------------------------------------- writing

def write_requests(w):
    body = {"customer_name": "Yeni", "items": [], "subtotal": 1, "tax_rate": 0, "tax_amount": 0, "total_amount": 1}
    return [
        ("post", url(w), {"json": body}),
        ("patch", url(w, f"/{w.draft.id}"), {"json": {"notes": "x"}}),
        ("post", url(w, f"/{w.draft.id}/pay"), {"params": {"payment_method": "CASH"}}),
        ("post", url(w, f"/{w.draft.id}/cancel"), {}),
        ("post", url(w, f"/from-appointment/{w.appt.id}"), {}),
    ]


@pytest.mark.parametrize("role", OTHERS)
def test_other_roles_cannot_write_invoices(client, w, role, db):
    for method, path, kwargs in write_requests(w):
        res = getattr(client, method)(path, headers=as_(w, role), **kwargs)
        assert res.status_code == 403, (method, path, res.text)
    db.refresh(w.draft)
    assert w.draft.status == InvoiceStatus.DRAFT and w.draft.notes is None


@pytest.mark.parametrize("role", FINANCE)
def test_finance_roles_can_write_invoices(client, w, role):
    for method, path, kwargs in write_requests(w):
        if path.endswith("/cancel"):
            continue  # pay already moved the draft on
        res = getattr(client, method)(path, headers=as_(w, role), **kwargs)
        assert res.status_code in (200, 201), (method, path, res.text)
        assert res.json()["total_amount"] is not None


# ---------------------------------------------------------------- pending agent actions

def pending_types(client, w, role):
    res = client.get(f"{API}/businesses/{w.biz.id}/agent-actions/pending", headers=as_(w, role))
    assert res.status_code == 200
    return {row["action_type"] for row in res.json()}


@pytest.mark.parametrize("role", FINANCE)
def test_finance_roles_see_finance_drafts(client, w, role):
    assert pending_types(client, w, role) == {"CREATE_INVOICE", "CREATE_EXPENSE", "CREATE_CAMPAIGN"}


@pytest.mark.parametrize("role", OTHERS)
def test_other_roles_do_not_see_finance_drafts(client, w, role):
    assert pending_types(client, w, role) == {"CREATE_CAMPAIGN"}


# ---------------------------------------------------------------- /me

@pytest.mark.parametrize("role,finance", [("owner", True), ("admin", True), ("employee", False), ("viewer", False)])
def test_me_reports_role_and_finance_access(client, w, role, finance):
    body = client.get(f"{API}/businesses/{w.biz.id}/me", headers=as_(w, role)).json()
    assert body == {"role": role.upper(), "can_view_finance": finance}


def test_me_rejects_non_members(client, w, db):
    stranger = User(first_name="S", last_name="X", email=f"s-{uuid.uuid4().hex[:6]}@test.local", password_hash="x",
                    status=UserStatus.ACTIVE)
    db.add(stranger)
    db.commit()
    assert client.get(f"{API}/businesses/{w.biz.id}/me", headers=auth(stranger)).status_code in (403, 404)
