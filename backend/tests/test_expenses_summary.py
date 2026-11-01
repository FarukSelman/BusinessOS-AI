"""
Monthly financial summary behind the expenses page cards.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.business.models import Business
from app.modules.expenses.models import Expense
from app.modules.membership.models import Membership
from app.modules.user.models import User
from app.shared.enums.expense import TransactionDirection
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

INCOME = TransactionDirection.INCOME
EXPENSE = TransactionDirection.EXPENSE


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
    biz = Business(name="Özet", slug=f"ozet-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(biz)
    db.flush()
    db.add(Membership(user_id=owner.id, business_id=biz.id, role=MembershipRole.OWNER))

    def add(day, direction, amount, deleted=False):
        db.add(Expense(business_id=biz.id, direction=direction, title="x", amount=Decimal(amount),
                       transaction_date=day, is_deleted=deleted))

    add(date(2026, 10, 31), INCOME, 1000)          # previous month's last day
    add(date(2026, 11, 1), INCOME, 200)            # first day
    add(date(2026, 11, 30), INCOME, 50)            # last day
    add(date(2026, 11, 10), EXPENSE, 999, deleted=True)
    add(date(2026, 12, 1), EXPENSE, 5)             # next month
    for _ in range(25):                            # more than one default list page
        add(date(2026, 11, 15), EXPENSE, 4)
    db.commit()
    return owner, biz


def test_month_summary_counts_every_transaction_of_the_month(client, world):
    owner, biz = world
    res = client.get(f"{API}/businesses/{biz.id}/expenses/summary",
                     params={"start_date": "2026-11-01", "end_date": "2026-11-30"}, headers=auth(owner))
    assert res.status_code == 200
    body = res.json()
    assert body["total_income"] == 250.0
    assert body["total_expense"] == 100.0
    assert body["net_profit"] == 150.0
    assert body["transaction_count"] == 27


def test_empty_month_has_zero_count(client, world):
    owner, biz = world
    res = client.get(f"{API}/businesses/{biz.id}/expenses/summary",
                     params={"start_date": "2026-01-01", "end_date": "2026-01-31"}, headers=auth(owner))
    assert res.json()["transaction_count"] == 0
    assert res.json()["total_income"] == 0.0
