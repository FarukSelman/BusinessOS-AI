"""
Customer package list: paging with X-Total-Count and server-side search.

The page used to receive the default 20 rows and filter only those on the
client, so a package sold earlier could not be found. Search now runs in the
backend over every customer package (customer name, package name, customer
phone by digits), like the customer, invoice and expense lists.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.business.models import Business
from app.modules.customers.models import Customer
from app.modules.membership.models import Membership
from app.modules.packages.models import CustomerPackage, ServicePackage
from app.modules.user.models import User
from app.shared.enums.membership import MembershipRole
from app.shared.enums.package import CustomerPackageStatus
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

FILLERS = 25


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
    w.biz = Business(name="Paket Liste", slug=f"pl-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    w.owner = User(first_name="O", last_name="X", email=f"o-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    db.add(w.owner)
    db.flush()
    db.add(Membership(user_id=w.owner.id, business_id=w.biz.id, role=MembershipRole.OWNER))

    def package(name):
        return ServicePackage(business_id=w.biz.id, name=name, services=[], total_sessions=4, price=Decimal(1000))

    w.skin, w.hair = package("Cilt Bakımı 4 Seans"), package("Saç %50 İndirimli")
    db.add_all([w.skin, w.hair])
    old = Customer(business_id=w.biz.id, name="IŞIK Özdemir", phone="0532 999 88 77")
    fillers = [Customer(business_id=w.biz.id, name=f"Müşteri {i:02d}", phone=f"0500 000 00 {i:02d}") for i in range(FILLERS)]
    db.add_all([old, *fillers])
    db.flush()

    base = datetime(2026, 1, 1, tzinfo=UTC)

    def sold(customer, pkg, minutes, status=CustomerPackageStatus.ACTIVE):
        return CustomerPackage(business_id=w.biz.id, customer_id=customer.id, package_id=pkg.id, total_sessions=4,
                               remaining_sessions=4, total_price=Decimal(1000), paid_amount=Decimal(0), status=status,
                               created_at=base + timedelta(minutes=minutes))

    # The old customer's package is the oldest: not on page 1 of the unfiltered list.
    db.add(sold(old, w.skin, -60, CustomerPackageStatus.COMPLETED))
    db.add_all([sold(c, w.hair if i % 5 == 0 else w.skin, i) for i, c in enumerate(fillers)])
    db.commit()
    return w


def page(client, w, **params):
    res = client.get(f"{API}/businesses/{w.biz.id}/customer-packages", params=params, headers=auth(w.owner))
    assert res.status_code == 200, res.text
    return res.json(), int(res.headers["X-Total-Count"])


def test_pages_carry_total_count(client, w):
    rows, total = page(client, w)
    assert total == FILLERS + 1 and len(rows) == 20
    rows2, _ = page(client, w, page=2)
    assert len(rows2) == FILLERS + 1 - 20
    assert not {r["id"] for r in rows} & {r["id"] for r in rows2}
    assert rows2[-1]["customer_name"] == "IŞIK Özdemir"  # newest first, the old sale last


@pytest.mark.parametrize("term", ["ışık", "isik", "ozdemir", "999 88", "0532-999"])
def test_search_finds_a_package_beyond_the_first_page(client, w, term):
    rows, total = page(client, w, search=term)
    assert total == 1 and [r["customer_name"] for r in rows] == ["IŞIK Özdemir"]
    assert rows[0]["package_name"] == "Cilt Bakımı 4 Seans"


def test_search_by_package_name_and_literal_percent(client, w):
    _, total = page(client, w, search="sac")
    assert total == FILLERS // 5
    rows, total = page(client, w, search="%50")
    assert total == FILLERS // 5 and all(r["package_name"] == "Saç %50 İndirimli" for r in rows)
    assert page(client, w, search="%")[1] == FILLERS // 5  # % is literal, not a wildcard


def test_search_combines_with_status(client, w):
    assert page(client, w, search="isik", status="ACTIVE")[1] == 0
    assert page(client, w, search="isik", status="COMPLETED")[1] == 1
    assert page(client, w, status="ACTIVE")[1] == FILLERS
