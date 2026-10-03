"""
Shared helpers for agent tools.

Every tool is bound to one business at construction time (business_id comes
from the authenticated request, never from the LLM), so a tool can only ever
read or draft data of that business.
"""
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.agents.tools.base import BaseTool
from app.shared.enums.membership import MembershipRole

# Roles allowed to see money: revenue, expenses, cash, installments, spend per customer.
FINANCE_ROLES = {MembershipRole.OWNER, MembershipRole.ADMIN}

MAX_ROWS = 20

PERIOD_PARAMETER = {
    "type": "string",
    "enum": ["today", "week", "month", "last_month", "quarter", "year"],
    "description": (
        "Dönem: today=bugün, week=son 7 gün, month=bu ay, last_month=geçen ay, "
        "quarter=son 90 gün, year=bu yıl"
    ),
}

PERIOD_LABELS = {
    "today": "Bugün",
    "week": "Son 7 gün",
    "month": "Bu ay",
    "last_month": "Geçen ay",
    "quarter": "Son 90 gün",
    "year": "Bu yıl",
}


def can_view_finance(role) -> bool:
    if role is None:
        return False
    try:
        return MembershipRole(role) in FINANCE_ROLES
    except ValueError:
        return False


def resolve_period(period: str | None, default: str = "month", today: date | None = None) -> tuple[date, date, str]:
    """Turns a period keyword into (start, end, label). Unknown values fall back to `default`."""
    today = today or date.today()
    period = period if period in PERIOD_LABELS else default
    if period == "today":
        start = today
    elif period == "week":
        start = today - timedelta(days=6)
    elif period == "month":
        start = today.replace(day=1)
    elif period == "last_month":
        end = today.replace(day=1) - timedelta(days=1)
        return end.replace(day=1), end, PERIOD_LABELS[period]
    elif period == "quarter":
        start = today - timedelta(days=89)
    else:  # year
        start = today.replace(month=1, day=1)
    return start, today, PERIOD_LABELS[period]


def money(value) -> str:
    """1234.5 -> '1.234,50 TL'"""
    text = f"{float(value or 0):,.2f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".") + " TL"


def find_customer(db: Session, business_id: UUID, name: str):
    """
    Finds exactly one active customer of the business by name.
    Returns (customer, None) or (None, error message for the LLM).
    """
    from app.modules.customers.models import Customer
    from app.shared.enums.customer import CustomerStatus

    name = (name or "").strip()
    if not name:
        return None, "Müşteri adı gerekli."
    base = db.query(Customer).filter(
        Customer.business_id == business_id,
        Customer.status == CustomerStatus.ACTIVE,
        Customer.is_deleted.is_(False),
    )
    matches = base.filter(Customer.name.ilike(name)).all()
    if not matches:
        matches = base.filter(Customer.name.ilike(f"%{name}%")).limit(6).all()
    if not matches:
        return None, f"'{name}' adında aktif müşteri bulunamadı."
    if len(matches) > 1:
        names = ", ".join(c.name for c in matches[:5])
        return None, f"'{name}' için birden fazla müşteri bulundu: {names}. Lütfen tam adı belirtin."
    return matches[0], None


class BusinessTool(BaseTool):
    """Base for tools bound to a single business (and optionally a user and role)."""

    def __init__(self, db: Session, business_id: UUID, role=None, user_id: UUID | None = None):
        self.db = db
        self.business_id = business_id
        self.role = role
        self.user_id = user_id

    @property
    def can_view_finance(self) -> bool:
        return can_view_finance(self.role)
