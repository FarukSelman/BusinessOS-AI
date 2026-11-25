"""
Finance report (/reports/finance), the revenue report and the dashboard's
"this month" money, on local (Europe/Istanbul) days.

The database session runs in UTC; these tests pin the day boundaries that used
to slip (an invoice paid at 00:30 on 1 November in Istanbul is 21:30 UTC on 31
October and must count for November).

Integration tests use PostgreSQL and are skipped when it is unreachable.
"""
import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from unittest import mock
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.appointments.models import Appointment
from app.modules.business.models import Business
from app.modules.customers.models import Customer
from app.modules.expense_categories.models import ExpenseCategory
from app.modules.expenses.models import Expense
from app.modules.invoice.models import Invoice
from app.modules.membership.models import Membership
from app.modules.packages.models import CustomerPackage, Installment, ServicePackage
from app.modules.products.models import ProductSale
from app.modules.services.models import Service
from app.modules.user.models import User
from app.shared.enums.expense import ExpenseStatus, TransactionDirection
from app.shared.enums.invoice import InvoiceStatus
from app.shared.enums.membership import MembershipRole
from app.shared.enums.package import InstallmentStatus
from app.shared.enums.user import UserStatus
from tests.pg_support import API, auth, make_client, make_engine, release_client

IST = ZoneInfo("Europe/Istanbul")


def ist(y, m, d, hh=12, mm=0):
    """A moment in Istanbul, stored as UTC like the app does."""
    return datetime(y, m, d, hh, mm, tzinfo=IST).astimezone(UTC)


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
    w.biz = Business(name="Finans", slug=f"fn-{sfx}", industry="beauty", email=f"b-{sfx}@example.com", phone="0")
    db.add(w.biz)
    db.flush()
    for role in MembershipRole:
        u = User(first_name=role.value.title(), last_name="Test", email=f"{role.value.lower()}-{sfx}@test.local",
                 password_hash="x", status=UserStatus.ACTIVE)
        db.add(u)
        db.flush()
        db.add(Membership(user_id=u.id, business_id=w.biz.id, role=role))
        setattr(w, role.value.lower(), u)

    b = w.biz.id
    cut = Service(business_id=b, name="Saç Kesimi", price=Decimal(300))
    customer = Customer(business_id=b, name="Ayşe Kaya")
    db.add_all([cut, customer])
    db.flush()
    appt = Appointment(business_id=b, customer_id=customer.id, customer_name="Ayşe Kaya", service_id=cut.id,
                       appointment_date=date(2026, 11, 1), start_time=time(10))
    db.add(appt)
    db.flush()

    def invoice(no, amount, paid_at, appointment=None, status=InvoiceStatus.PAID):
        return Invoice(business_id=b, customer_name="Ayşe Kaya", invoice_number=f"{no}-{sfx}", items=[],
                       subtotal=Decimal(amount), tax_rate=0, tax_amount=0, total_amount=Decimal(amount),
                       status=status, paid_at=paid_at, appointment_id=appointment.id if appointment else None)

    db.add_all([
        invoice("A", 300, ist(2026, 11, 1, 0, 30), appt),   # 21:30 UTC on 31 Oct -> November
        invoice("B", 200, ist(2026, 10, 31, 23, 30)),       # 20:30 UTC on 31 Oct -> October
        invoice("C", 150, ist(2026, 11, 12)),               # no appointment
        invoice("D", 999, None, status=InvoiceStatus.SENT),  # not paid: never counted
    ])
    db.add(ProductSale(business_id=b, sale_date=ist(2026, 11, 3, 18), total_amount=Decimal(240),
                       items=[{"product_id": str(uuid.uuid4()), "product_name": "Şampuan", "quantity": 2, "total": 240}]))
    pkg = ServicePackage(business_id=b, name="Paket", services=[], total_sessions=4, price=Decimal(1000))
    db.add(pkg)
    db.flush()
    cp = CustomerPackage(business_id=b, customer_id=customer.id, package_id=pkg.id, total_sessions=4,
                         remaining_sessions=4, total_price=Decimal(1000), paid_amount=Decimal(500))
    db.add(cp)
    db.flush()
    db.add_all([
        Installment(customer_package_id=cp.id, business_id=b, customer_id=customer.id, installment_number=1,
                    amount=Decimal(500), due_date=date(2026, 11, 10), paid_date=date(2026, 11, 10),
                    status=InstallmentStatus.PAID),
        Installment(customer_package_id=cp.id, business_id=b, customer_id=customer.id, installment_number=2,
                    amount=Decimal(500), due_date=date(2026, 12, 10), status=InstallmentStatus.PENDING),
    ])
    rent = ExpenseCategory(business_id=b, name="Kira", color="#ef4444")
    db.add(rent)
    db.flush()

    def entry(direction, amount, day, category=None, status=ExpenseStatus.PAID):
        return Expense(business_id=b, direction=direction, title="x", amount=Decimal(amount), transaction_date=day,
                       category_id=category.id if category else None, status=status)

    db.add_all([
        entry(TransactionDirection.EXPENSE, 1000, date(2026, 11, 2), rent),
        entry(TransactionDirection.EXPENSE, 80, date(2026, 11, 20)),                    # no category
        entry(TransactionDirection.EXPENSE, 5000, date(2026, 11, 21), rent, ExpenseStatus.CANCELLED),
        entry(TransactionDirection.EXPENSE, 400, date(2026, 10, 15), rent),
        entry(TransactionDirection.EXPENSE, 70, date(2026, 12, 1)),                     # next month
        entry(TransactionDirection.INCOME, 100, date(2026, 11, 25)),                     # entered by hand
    ])
    db.commit()
    return w


def report(client, w, user=None, **params):
    params = {"start_date": "2026-11-01", "end_date": "2026-11-30", "group_by": "month", **params}
    return client.get(f"{API}/businesses/{w.biz.id}/reports/finance", params=params, headers=auth(user or w.owner))


# ---------------------------------------------------------------- local days (regressions)

def test_invoice_paid_at_0030_istanbul_counts_for_november(client, w):
    nov = report(client, w).json()
    assert nov["totals"]["invoices"] == 450.0  # A (00:30 on 1 Nov) + C; not B (23:30 on 31 Oct)
    oct_ = report(client, w, start_date="2026-10-01", end_date="2026-10-31").json()
    assert oct_["totals"]["invoices"] == 200.0


def test_revenue_report_puts_the_0030_invoice_in_november(client, w):
    res = client.get(f"{API}/businesses/{w.biz.id}/reports/revenue", headers=auth(w.owner),
                     params={"start_date": "2026-10-01", "end_date": "2026-11-30", "group_by": "month"})
    assert res.status_code == 200, res.text
    rows = {r["period"]: r for r in res.json()}
    assert list(rows) == ["2026-10-01", "2026-11-01"]  # ordered, one row per month
    assert rows["2026-10-01"]["invoice_count"] == 1 and rows["2026-11-01"]["invoice_count"] == 2
    assert rows["2026-11-01"]["income"] == 450 + 240 + 500 + 100  # every income source
    assert rows["2026-11-01"]["expense"] == 1080.0


def test_revenue_report_understands_the_frontend_group_names(client, w):
    """The page sent week/month while the API only knew weekly/monthly, so it always grouped by day."""
    for name in ("month", "monthly"):
        res = client.get(f"{API}/businesses/{w.biz.id}/reports/revenue", headers=auth(w.owner),
                         params={"start_date": "2026-10-01", "end_date": "2026-11-30", "group_by": name})
        assert [r["period"] for r in res.json()] == ["2026-10-01", "2026-11-01"]


def test_dashboard_this_month_uses_local_days_and_ends_with_the_month(client, w):
    with mock.patch("app.modules.reports.service.local_today", return_value=date(2026, 11, 15)):
        stats = client.get(f"{API}/businesses/{w.biz.id}/reports/dashboard-stats", headers=auth(w.owner)).json()
    assert stats["total_revenue_this_month"] == 450 + 240 + 500 + 100  # A counted, B not
    assert stats["total_expenses_this_month"] == 1080.0  # December's 70 and the cancelled 5000 not counted
    assert stats["net_profit_this_month"] == 1290 - 1080


# ---------------------------------------------------------------- series

def test_sources_are_kept_apart_and_add_up(client, w):
    t = report(client, w).json()["totals"]
    assert (t["invoices"], t["product_sales"], t["installments"], t["other_income"]) == (450, 240, 500, 100)
    assert t["income"] == 1290 and t["expense"] == 1080 and t["net"] == 210


def test_daily_series_is_zero_filled_and_ordered(client, w):
    series = report(client, w, group_by="day").json()["series"]
    assert [s["period"] for s in series] == [date(2026, 11, d).isoformat() for d in range(1, 31)]
    by_day = {s["period"]: s for s in series}
    assert by_day["2026-11-01"]["invoices"] == 300 and by_day["2026-11-02"]["expense"] == 1000
    assert by_day["2026-11-05"] == {**by_day["2026-11-05"], "income": 0, "expense": 0, "net": 0}


def test_weekly_series_starts_on_monday(client, w):
    series = report(client, w, group_by="week").json()["series"]
    starts = [s["period"] for s in series]
    assert starts[0] == "2026-10-26"  # the Monday of the week holding 1 November
    assert all(date.fromisoformat(p).weekday() == 0 for p in starts)
    assert sum(s["income"] for s in series) == 1290


def test_previous_period_is_the_same_length_right_before(client, w):
    prev = report(client, w).json()["previous"]
    assert (prev["start_date"], prev["end_date"]) == ("2026-10-02", "2026-10-31")
    assert prev["invoices"] == 200 and prev["expense"] == 400


# ---------------------------------------------------------------- breakdowns

def test_expense_by_category(client, w):
    rows = report(client, w).json()["expense_by_category"]
    assert [(r["name"], r["amount"]) for r in rows] == [("Kira", 1000.0), ("Kategorisiz", 80.0)]
    assert rows[0]["color"] == "#ef4444"


def test_revenue_by_service_and_product(client, w):
    body = report(client, w).json()
    services = {r["name"]: r for r in body["revenue_by_service"]}
    assert services["Saç Kesimi"]["amount"] == 300 and services["Saç Kesimi"]["count"] == 1
    assert services["Randevuya bağlı olmayan faturalar"]["amount"] == 150
    assert body["revenue_by_product"] == [{"name": "Şampuan", "amount": 240.0, "quantity": 2}]


def test_empty_range_is_all_zero(client, w):
    body = report(client, w, start_date="2025-01-01", end_date="2025-01-31").json()
    assert body["totals"]["income"] == 0 and body["expense_by_category"] == []
    assert len(body["series"]) == 1 and body["series"][0]["net"] == 0


# ---------------------------------------------------------------- limits and roles

@pytest.mark.parametrize("params, message", [
    ({"group_by": "day", "start_date": "2026-01-01", "end_date": "2026-04-30"},
     "Günlük gruplama en fazla 92 gün için kullanılabilir; daha uzun aralıklarda haftalık veya aylık gruplamayı seçin."),
    ({"start_date": "2026-11-30", "end_date": "2026-11-01"}, "Bitiş tarihi başlangıçtan önce olamaz."),
    ({"start_date": "2020-01-01", "end_date": "2026-01-31"}, "Tarih aralığı en fazla 5 yıl olabilir."),
    ({"group_by": "year"}, "Gruplama günlük, haftalık veya aylık olmalı."),
])
def test_bad_ranges_get_a_turkish_422(client, w, params, message):
    res = report(client, w, **params)
    assert res.status_code == 422 and res.json()["message"] == message


def test_92_days_is_still_fine_daily(client, w):
    assert report(client, w, group_by="day", start_date="2026-09-01", end_date="2026-12-01").status_code == 200


@pytest.mark.parametrize("role, code", [("owner", 200), ("admin", 200), ("employee", 403), ("viewer", 403)])
def test_only_owner_and_admin_see_the_finance_report(client, w, role, code):
    res = report(client, w, getattr(w, role))
    assert res.status_code == code
    if code == 403:
        assert res.json()["message"] == "Bu işlem yalnızca işletme sahibi ve yöneticilere açıktır."
