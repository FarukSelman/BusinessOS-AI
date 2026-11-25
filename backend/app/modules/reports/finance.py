"""
Finance report: income by source, expenses, net, breakdowns and the previous
period, all on local calendar days.

Local days: the database session runs in UTC, so date(paid_at) put an invoice
paid at 00:30 in Istanbul on the previous day (and month). Every timestamp is
first converted to APP_TIMEZONE in SQL (timezone(tz, col)); `date` columns
(expense and installment dates) are already local.

Income sources are kept apart. None of them creates another automatically
(a product sale, package sale or installment payment writes no invoice and no
income entry; a paid invoice writes no income entry), but an income entered
by hand can repeat an invoice, which the page says.

/reports/finance, /reports/revenue and the dashboard's "this month" figures
all use income_expense_series / totals below.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import Date, and_, cast, column, func, select, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.appointments.models import Appointment
from app.modules.expense_categories.models import ExpenseCategory
from app.modules.expenses.models import Expense
from app.modules.invoice.models import Invoice
from app.modules.packages.models import Installment
from app.modules.products.models import ProductSale
from app.modules.services.models import Service
from app.shared.enums.expense import ExpenseStatus, TransactionDirection
from app.shared.enums.invoice import InvoiceStatus
from app.shared.enums.package import InstallmentStatus

GROUPS = {"day": "day", "daily": "day", "week": "week", "weekly": "week", "month": "month", "monthly": "month"}
MAX_DAILY_DAYS = 92
MAX_RANGE_DAYS = 5 * 366
TOP_N = 10
SOURCES = ("invoices", "product_sales", "installments", "other_income")


# ---------------------------------------------------------------- dates

def local_today() -> date:
    return datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date()


def local_date(column):
    """A timestamptz column as the calendar day in APP_TIMEZONE."""
    return cast(func.timezone(settings.APP_TIMEZONE, column), Date)


def normalize_group(group_by: str) -> str:
    try:
        return GROUPS[group_by]
    except KeyError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Gruplama günlük, haftalık veya aylık olmalı.") from None


def check_range(start: date, end: date, group: str) -> None:
    if end < start:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Bitiş tarihi başlangıçtan önce olamaz.")
    days = (end - start).days + 1
    if days > MAX_RANGE_DAYS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Tarih aralığı en fazla 5 yıl olabilir.")
    if group == "day" and days > MAX_DAILY_DAYS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Günlük gruplama en fazla {MAX_DAILY_DAYS} gün için kullanılabilir; "
            "daha uzun aralıklarda haftalık veya aylık gruplamayı seçin.",
        )


def period_start(day: date, group: str) -> date:
    if group == "week":
        return day - timedelta(days=day.weekday())  # Monday, like Postgres date_trunc('week')
    if group == "month":
        return day.replace(day=1)
    return day


def periods(start: date, end: date, group: str) -> list[date]:
    out, current = [], period_start(start, group)
    while current <= end:
        out.append(current)
        if group == "day":
            current += timedelta(days=1)
        elif group == "week":
            current += timedelta(days=7)
        else:
            current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    return out


def previous_range(start: date, end: date) -> tuple[date, date]:
    """The equally long range right before [start, end]."""
    length = (end - start).days + 1
    return start - timedelta(days=length), start - timedelta(days=1)


def month_range(day: date) -> tuple[date, date]:
    first = day.replace(day=1)
    next_first = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first, next_first - timedelta(days=1)


# ---------------------------------------------------------------- queries

def _amount_by_period(db: Session, amount, day, where, start: date, end: date, group: str) -> dict[date, float]:
    bucket = cast(func.date_trunc(group, day), Date)
    rows = db.execute(
        select(bucket.label("p"), func.sum(amount)).where(*where, day >= start, day <= end).group_by("p")
    ).all()
    return {p: float(total or 0) for p, total in rows}


def _sources(business_id):
    """(name, amount column, local-day expression, filters) for each income source and expenses."""
    return {
        "invoices": (Invoice.total_amount, local_date(Invoice.paid_at),
                     [Invoice.business_id == business_id, Invoice.is_deleted.is_(False),
                      Invoice.status == InvoiceStatus.PAID]),
        "product_sales": (ProductSale.total_amount, local_date(ProductSale.sale_date),
                          [ProductSale.business_id == business_id, ProductSale.is_deleted.is_(False)]),
        "installments": (Installment.amount, Installment.paid_date,
                         [Installment.business_id == business_id, Installment.is_deleted.is_(False),
                          Installment.status == InstallmentStatus.PAID]),
        "other_income": (Expense.amount, Expense.transaction_date,
                         [Expense.business_id == business_id, Expense.is_deleted.is_(False),
                          Expense.direction == TransactionDirection.INCOME,
                          Expense.status != ExpenseStatus.CANCELLED]),
        "expense": (Expense.amount, Expense.transaction_date,
                    [Expense.business_id == business_id, Expense.is_deleted.is_(False),
                     Expense.direction == TransactionDirection.EXPENSE,
                     Expense.status != ExpenseStatus.CANCELLED]),
    }


def _row(values: dict) -> dict:
    income = round(sum(values.get(s, 0.0) for s in SOURCES), 2)
    expense = round(values.get("expense", 0.0), 2)
    row = {s: round(values.get(s, 0.0), 2) for s in SOURCES}
    return {**row, "income": income, "expense": expense, "net": round(income - expense, 2)}


def income_expense_series(db: Session, business_id, start: date, end: date, group: str) -> list[dict]:
    """One row per period from start to end (zero-filled, oldest first)."""
    by_source = {
        name: _amount_by_period(db, amount, day, where, start, end, group)
        for name, (amount, day, where) in _sources(business_id).items()
    }
    return [
        {"period": p, **_row({name: values.get(p, 0.0) for name, values in by_source.items()})}
        for p in periods(start, end, group)
    ]


def totals(db: Session, business_id, start: date, end: date) -> dict:
    values = {}
    for name, (amount, day, where) in _sources(business_id).items():
        values[name] = float(db.scalar(select(func.sum(amount)).where(*where, day >= start, day <= end)) or 0)
    return _row(values)


def expense_by_category(db: Session, business_id, start: date, end: date) -> list[dict]:
    _, day, where = _sources(business_id)["expense"]
    name = func.coalesce(ExpenseCategory.name, "Kategorisiz")
    rows = db.execute(
        select(name.label("name"), ExpenseCategory.color, func.sum(Expense.amount), func.count(Expense.id))
        .outerjoin(ExpenseCategory, ExpenseCategory.id == Expense.category_id)
        .where(*where, day >= start, day <= end)
        .group_by(name, ExpenseCategory.color)
        .order_by(func.sum(Expense.amount).desc())
    ).all()
    return [{"name": n, "color": c, "amount": round(float(a or 0), 2), "count": k} for n, c, a, k in rows]


def _top(rows: list[dict], key: str) -> list[dict]:
    rows = sorted(rows, key=lambda r: r["amount"], reverse=True)
    if len(rows) <= TOP_N:
        return rows
    head, tail = rows[:TOP_N - 1], rows[TOP_N - 1:]
    other = {"name": "Diğer", "amount": round(sum(r["amount"] for r in tail), 2), key: sum(r[key] for r in tail)}
    return head + [other]


def revenue_by_service(db: Session, business_id, start: date, end: date) -> list[dict]:
    """Paid invoices by the service of their appointment; the rest in one row."""
    _, day, where = _sources(business_id)["invoices"]
    name = func.coalesce(Service.name, "Randevuya bağlı olmayan faturalar")
    rows = db.execute(
        select(name.label("name"), func.sum(Invoice.total_amount), func.count(Invoice.id))
        .outerjoin(Appointment, and_(Appointment.id == Invoice.appointment_id, Appointment.is_deleted.is_(False)))
        .outerjoin(Service, Service.id == Appointment.service_id)
        .where(*where, day >= start, day <= end)
        .group_by(name)
    ).all()
    return _top([{"name": n, "amount": round(float(a or 0), 2), "count": k} for n, a, k in rows], "count")


def revenue_by_product(db: Session, business_id, start: date, end: date) -> list[dict]:
    """Product sale lines (name, quantity, line total incl. tax)."""
    _, day, where = _sources(business_id)["product_sales"]
    item = func.jsonb_array_elements(ProductSale.items).table_valued(column("value", JSONB)).render_derived()
    name = item.c.value["product_name"].astext
    rows = db.execute(
        select(
            name.label("name"),
            func.sum(cast(item.c.value["total"].astext, ProductSale.total_amount.type)),
            func.sum(cast(item.c.value["quantity"].astext, ProductSale.total_amount.type)),
        )
        .select_from(ProductSale)
        .join(item, true())  # LATERAL over the sale's own items
        .where(*where, day >= start, day <= end)
        .group_by(name)
    ).all()
    return _top([{"name": n or "Adsız ürün", "amount": round(float(a or 0), 2), "quantity": int(q or 0)}
                 for n, a, q in rows], "quantity")


def finance_report(db: Session, business_id, start: date, end: date, group_by: str) -> dict:
    group = normalize_group(group_by)
    check_range(start, end, group)
    prev_start, prev_end = previous_range(start, end)
    return {
        "start_date": start,
        "end_date": end,
        "group_by": group,
        "series": income_expense_series(db, business_id, start, end, group),
        "totals": totals(db, business_id, start, end),
        "previous": {"start_date": prev_start, "end_date": prev_end, **totals(db, business_id, prev_start, prev_end)},
        "expense_by_category": expense_by_category(db, business_id, start, end),
        "revenue_by_service": revenue_by_service(db, business_id, start, end),
        "revenue_by_product": revenue_by_product(db, business_id, start, end),
    }
