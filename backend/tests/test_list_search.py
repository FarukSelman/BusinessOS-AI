"""
Search, filters and X-Total-Count on the customer, invoice and expense lists.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.modules.business.models import Business
from app.modules.customer_tags.models import CustomerTag, CustomerTagAssignment
from app.modules.customers.models import Customer
from app.modules.expenses.models import Expense
from app.modules.invoice.models import Invoice
from app.modules.membership.models import Membership
from app.modules.user.models import User
from app.shared.enums.customer import CustomerStatus
from app.shared.enums.expense import TransactionDirection
from app.shared.enums.invoice import InvoiceStatus
from app.shared.enums.membership import MembershipRole
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


def make_world(db) -> World:
    sfx = uuid.uuid4().hex[:8]
    w = World()
    w.owner = User(first_name="O", last_name="X", email=f"o-{sfx}@test.local", password_hash="x", status=UserStatus.ACTIVE)
    db.add(w.owner)
    db.flush()
    w.biz = Business(name="Arama", slug=f"arama-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    db.add(Membership(user_id=w.owner.id, business_id=w.biz.id, role=MembershipRole.OWNER))

    def customer(name, phone=None, email=None, created=datetime(2026, 10, 1, 9, tzinfo=UTC), status=CustomerStatus.ACTIVE):
        c = Customer(business_id=w.biz.id, name=name, phone=phone, email=email, created_at=created, status=status)
        db.add(c)
        return c

    w.ayse = customer("Ayşe Yılmaz", phone="0555 123 45 67", email="ayse@example.com")
    w.isik = customer("IŞIK Kaya", phone="+90 532 000 11 22")
    w.ilgin = customer("ılgın Demir")
    w.literal = customer("50%_Ali")
    w.passive = customer("Pasif Müşteri", status=CustomerStatus.INACTIVE)
    # 23:30 in Istanbul on 31 Oct is 20:30 UTC: belongs to 31 Oct locally.
    w.late = customer("Geç Kayıt", created=datetime(2026, 10, 31, 20, 30, tzinfo=UTC))
    for i in range(FILLERS):
        customer(f"Dolgu {i:02d}")
    db.flush()

    w.vip = CustomerTag(business_id=w.biz.id, name="VIP", color="#ff0000")
    db.add(w.vip)
    db.flush()
    db.add_all([CustomerTagAssignment(customer_id=w.ayse.id, tag_id=w.vip.id),
                CustomerTagAssignment(customer_id=w.isik.id, tag_id=w.vip.id)])

    for i, (number, name, status) in enumerate([("FT-2026-001", "Ayşe Yılmaz", InvoiceStatus.PAID),
                                                ("FT-2026-002", "Mehmet Öz", InvoiceStatus.DRAFT),
                                                ("FT-2026-003", "Ayşe Kara", InvoiceStatus.DRAFT)]):
        db.add(Invoice(business_id=w.biz.id, customer_name=name, invoice_number=f"{number}-{sfx}", items=[],
                       subtotal=Decimal(1), tax_rate=0, tax_amount=0, total_amount=Decimal(1), status=status))
    for i in range(FILLERS):
        db.add(Expense(business_id=w.biz.id, direction=TransactionDirection.EXPENSE, title=f"Kira {i:02d}",
                       amount=Decimal(1), transaction_date=date(2026, 10, 5)))
    db.add(Expense(business_id=w.biz.id, direction=TransactionDirection.EXPENSE, title="Elektrik faturası",
                   description="Ekim dönemi", amount=Decimal(1), transaction_date=date(2026, 10, 5)))
    db.commit()
    return w


def get(client, w, resource, user=None, **params):
    res = client.get(f"{API}/businesses/{w.biz.id}/{resource}", params=params, headers=auth(user or w.owner))
    return res


def names(res):
    return {r["name"] for r in res.json()}


# ---------------------------------------------------------------- customers

def test_total_count_header_and_page_size(client, db):
    w = make_world(db)
    res = get(client, w, "customers")
    assert res.status_code == 200
    assert res.headers["X-Total-Count"] == str(6 + FILLERS)
    assert len(res.json()) == 20


@pytest.mark.parametrize("term", ["ayse", "AYŞE", "Ayşe", "yılmaz", "YILMAZ"])
def test_turkish_letters_match_regardless_of_case_and_diacritics(client, db, term):
    w = make_world(db)
    assert names(get(client, w, "customers", search=term)) == {"Ayşe Yılmaz"}


def test_dotless_and_dotted_i_match_each_other(client, db):
    w = make_world(db)
    assert names(get(client, w, "customers", search="ışık")) == {"IŞIK Kaya"}
    assert names(get(client, w, "customers", search="ILGIN")) == {"ılgın Demir"}


@pytest.mark.parametrize("term", ["%", "_", "50%_"])
def test_like_wildcards_are_literal(client, db, term):
    w = make_world(db)
    res = get(client, w, "customers", search=term)
    assert names(res) == {"50%_Ali"}
    assert res.headers["X-Total-Count"] == "1"


@pytest.mark.parametrize("term", ["555 123", "05551234567", "532-000-11", "(532) 000"])
def test_phone_search_compares_digits(client, db, term):
    w = make_world(db)
    found = names(get(client, w, "customers", search=term))
    assert found and found <= {"Ayşe Yılmaz", "IŞIK Kaya"}


def test_rows_carry_their_tags_and_tag_filter_counts(client, db):
    w = make_world(db)
    res = get(client, w, "customers", tag_ids=[str(w.vip.id)])
    assert res.headers["X-Total-Count"] == "2"
    assert {r["name"]: [t["name"] for t in r["tags"]] for r in res.json()} == {
        "Ayşe Yılmaz": ["VIP"], "IŞIK Kaya": ["VIP"]}
    plain = next(r for r in get(client, w, "customers", search="Dolgu 01").json())
    assert plain["tags"] == []


def test_status_filter_and_search_combine(client, db):
    w = make_world(db)
    assert names(get(client, w, "customers", status="INACTIVE")) == {"Pasif Müşteri"}
    assert names(get(client, w, "customers", status="INACTIVE", search="ayse")) == set()


def test_date_to_includes_the_whole_local_day(client, db):
    w = make_world(db)
    assert "Geç Kayıt" in names(get(client, w, "customers", date_to="2026-10-31", size=100))
    assert names(get(client, w, "customers", date_from="2026-10-31")) == {"Geç Kayıt"}
    assert "Geç Kayıt" not in names(get(client, w, "customers", date_to="2026-10-30", size=100))


def test_other_business_cannot_search_customers(client, db):
    w = make_world(db)
    other = make_world(db)
    assert get(client, w, "customers", user=other.owner, search="ayse").status_code in (403, 404)


# ---------------------------------------------------------------- invoices

def test_invoice_search_by_number_and_customer(client, db):
    w = make_world(db)
    res = get(client, w, "invoices", search="ft-2026-002")
    assert [i["customer_name"] for i in res.json()] == ["Mehmet Öz"]
    res = get(client, w, "invoices", search="ayse")
    assert res.headers["X-Total-Count"] == "2"
    res = get(client, w, "invoices", search="ayse", status="PAID")
    assert [i["customer_name"] for i in res.json()] == ["Ayşe Yılmaz"]


# ---------------------------------------------------------------- expenses

def test_expense_search_title_and_description(client, db):
    w = make_world(db)
    assert [e["title"] for e in get(client, w, "expenses", search="ELEKTRİK").json()] == ["Elektrik faturası"]
    assert [e["title"] for e in get(client, w, "expenses", search="ekim donemi").json()] == ["Elektrik faturası"]
    assert get(client, w, "expenses").headers["X-Total-Count"] == str(FILLERS + 1)


def test_expense_pages_are_stable_when_dates_tie(client, db):
    w = make_world(db)
    seen = []
    for page in range(1, 10):
        rows = get(client, w, "expenses", page=page, size=4).json()
        seen += [r["id"] for r in rows]
        if len(rows) < 4:
            break
    assert len(seen) == len(set(seen)) == FILLERS + 1


# ---------------------------------------------------------------- browser

def test_total_count_header_is_exposed_to_the_browser(client, db):
    w = make_world(db)
    origin = settings.CORS_ORIGINS[0]
    res = client.get(f"{API}/businesses/{w.biz.id}/customers", headers={**auth(w.owner), "Origin": origin})
    assert "x-total-count" in res.headers.get("access-control-expose-headers", "").lower()
