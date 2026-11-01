"""
Income/expenses, expense categories and the cash register are finance-only:
owner/admin may read and write, employees and viewers get 403 on every
endpoint (reads too, since every field is money). Pattern: test_invoice_roles.py.

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.business.models import Business
from app.modules.cash_register.models import CashRegister, CashTransaction
from app.modules.expense_categories.models import ExpenseCategory
from app.modules.expenses.models import Expense
from app.modules.membership.models import Membership
from app.modules.user.models import User
from app.shared.enums.cash_register import CashRegisterStatus
from app.shared.enums.expense import TransactionDirection
from app.shared.enums.membership import MembershipRole
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

FINANCE = ["owner", "admin"]
OTHERS = ["employee", "viewer"]


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
    w.biz = Business(name="Finans", slug=f"fin-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
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
    w.category = ExpenseCategory(business_id=w.biz.id, name="Kira")
    db.add(w.category)
    db.flush()
    w.expense = Expense(business_id=w.biz.id, direction=TransactionDirection.EXPENSE, title="Maaş – Ayşe",
                        amount=Decimal(25000), transaction_date=date.today(), category_id=w.category.id)
    w.register = CashRegister(business_id=w.biz.id, register_date=date.today(), opening_balance=Decimal(500),
                              status=CashRegisterStatus.OPEN, opened_at=datetime.now(UTC))
    db.add_all([w.expense, w.register])
    db.commit()
    return w


def base(w):
    return f"{API}/businesses/{w.biz.id}"


def reads(w):
    b = base(w)
    today = date.today().isoformat()
    return [
        f"{b}/expenses",
        f"{b}/expenses/summary?start_date={today}&end_date={today}",
        f"{b}/expense-categories",
        f"{b}/cash-register/today",
        f"{b}/cash-register",
        f"{b}/cash-register/{w.register.id}",
        f"{b}/cash-register/{w.register.id}/summary",
    ]


def writes(w):
    b = base(w)
    expense = {"direction": "EXPENSE", "title": "Elektrik", "amount": 300, "transaction_date": date.today().isoformat()}
    return [
        ("post", f"{b}/expenses", {"json": expense}),
        ("patch", f"{b}/expenses/{w.expense.id}", {"json": {"title": "Değişti"}}),
        ("delete", f"{b}/expenses/{w.expense.id}", {}),
        ("post", f"{b}/expense-categories", {"json": {"name": "Yeni"}}),
        ("patch", f"{b}/expense-categories/{w.category.id}", {"json": {"name": "Değişti"}}),
        ("delete", f"{b}/expense-categories/{w.category.id}", {}),
        ("post", f"{b}/cash-register/open", {"json": {"opening_balance": 100}}),
        ("post", f"{b}/cash-register/{w.register.id}/transactions", {"json": {"transaction_type": "SALE", "amount": 50}}),
        ("post", f"{b}/cash-register/{w.register.id}/close", {"json": {"closing_balance": 550}}),
    ]


@pytest.mark.parametrize("role", FINANCE)
def test_finance_roles_can_read(client, w, role):
    for path in reads(w):
        res = client.get(path, headers=auth(getattr(w, role)))
        assert res.status_code == 200, (path, res.text)


@pytest.mark.parametrize("role", OTHERS)
def test_other_roles_cannot_read(client, w, role):
    for path in reads(w):
        res = client.get(path, headers=auth(getattr(w, role)))
        assert res.status_code == 403, (path, res.status_code)
        assert "Maaş" not in res.text and "25000" not in res.text


@pytest.mark.parametrize("role", FINANCE)
def test_finance_roles_can_write(client, w, role):
    for method, path, kwargs in writes(w):
        res = getattr(client, method)(path, headers=auth(getattr(w, role)), **kwargs)
        # Business rules may still say no (e.g. a register is already open today), but never "forbidden".
        assert res.status_code != 403 and res.status_code < 500, (method, path, res.status_code, res.text)


@pytest.mark.parametrize("role", OTHERS)
def test_other_roles_cannot_write_and_nothing_changes(client, w, db, role):
    def snapshot():
        return (
            db.scalar(select(func.count()).select_from(Expense).where(Expense.business_id == w.biz.id, Expense.is_deleted.is_(False))),
            db.scalar(select(func.count()).select_from(ExpenseCategory).where(ExpenseCategory.business_id == w.biz.id, ExpenseCategory.is_deleted.is_(False))),
            db.scalar(select(func.count()).select_from(CashTransaction).where(CashTransaction.business_id == w.biz.id)),
        )

    before = snapshot()
    for method, path, kwargs in writes(w):
        res = getattr(client, method)(path, headers=auth(getattr(w, role)), **kwargs)
        assert res.status_code == 403, (method, path, res.status_code)
    db.expire_all()
    assert snapshot() == before
    assert db.get(Expense, w.expense.id).title == "Maaş – Ayşe"
    assert db.get(CashRegister, w.register.id).status == CashRegisterStatus.OPEN
