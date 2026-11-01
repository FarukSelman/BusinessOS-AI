"""
Paged lists must be stable: the CSV export walks every page, so rows that tie
on the sort key must not repeat or go missing between pages.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.appointments.models import Appointment
from app.modules.business.models import Business
from app.modules.customers.models import Customer
from app.modules.invoice.models import Invoice
from app.modules.membership.models import Membership
from app.modules.user.models import User
from app.shared.enums.invoice import InvoiceStatus
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

ROWS = 23
PAGE = 5
SAME_MOMENT = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


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


@pytest.fixture
def world(db):
    sfx = uuid.uuid4().hex[:8]
    owner = User(first_name="O", last_name="X", email=f"o-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    db.add(owner)
    db.flush()
    biz = Business(name="Sayfa", slug=f"sayfa-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(biz)
    db.flush()
    db.add(Membership(user_id=owner.id, business_id=biz.id, role=MembershipRole.OWNER))
    # Every row ties on the sort key, the worst case for unstable paging.
    for i in range(ROWS):
        db.add(Appointment(business_id=biz.id, customer_name=f"R{i}", appointment_date=date(2026, 10, 1),
                           start_time=time(10)))
        db.add(Customer(business_id=biz.id, name=f"M{i}", created_at=SAME_MOMENT))
        db.add(Invoice(business_id=biz.id, customer_name=f"F{i}", invoice_number=f"INV-{sfx}-{i}", items=[],
                       subtotal=Decimal(1), tax_rate=0, tax_amount=0, total_amount=Decimal(1),
                       status=InvoiceStatus.DRAFT, created_at=SAME_MOMENT))
    db.commit()
    return owner, biz


def walk(client, url, headers):
    ids, page = [], 1
    while True:
        res = client.get(url, params={"page": page, "size": PAGE}, headers=headers)
        assert res.status_code == 200, res.text
        rows = res.json()
        ids += [r["id"] for r in rows]
        if len(rows) < PAGE:
            return ids
        page += 1


@pytest.mark.parametrize("resource", ["appointments", "customers", "invoices"])
def test_walking_all_pages_returns_every_row_exactly_once(client, world, resource):
    owner, biz = world
    ids = walk(client, f"{API}/businesses/{biz.id}/{resource}", auth(owner))
    assert len(ids) == ROWS
    assert len(set(ids)) == ROWS
