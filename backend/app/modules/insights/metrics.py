"""
Aggregated business metrics for the AI insights card.

PRIVACY: everything returned here is either a number, a date, a weekday /
hour, or a service name from the business's own catalogue. No query below
selects customer names, phones, e-mails, appointment notes or staff names;
staff are reported only as anonymous "Personel A/B/...". The dict returned
by build_metrics() is exactly what is sent to the language model, and
tests/test_insights.py asserts that no personal data can appear in it.

Periods: the last 30 days (today included) vs the 30 days before. Month to
date vs a whole previous month would report a fake "-80%" on the 5th.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import case, extract, func, select
from sqlalchemy.orm import Session

from app.modules.agent_actions.models import AgentAction
from app.modules.appointments.models import Appointment
from app.modules.customers.models import Customer
from app.modules.expenses.models import Expense
from app.modules.invoice.models import Invoice
from app.modules.services.models import Service
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.expense import TransactionDirection
from app.shared.enums.invoice import InvoiceStatus

PERIOD_DAYS = 30
WEEKDAYS_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
ONLINE_NOTE = "Online randevu sayfasından alındı."

# Below this the card shows "henüz yeterli veri yok" and no model is called.
MIN_APPOINTMENTS_60D = 5


@dataclass(frozen=True)
class Period:
    start: date
    end: date


def periods(today: date) -> tuple[Period, Period]:
    current = Period(today - timedelta(days=PERIOD_DAYS - 1), today)
    previous = Period(current.start - timedelta(days=PERIOD_DAYS), current.start - timedelta(days=1))
    return current, previous


def pct_change(current: float, previous: float) -> float | None:
    """Percent change rounded to 1 decimal; None when there is no base to compare with."""
    if not previous:
        return None
    return round((current - previous) / previous * 100.0, 1)


def _money(value) -> float:
    return round(float(value or 0), 2)


def _rate(part: int, whole: int) -> float | None:
    return round(part / whole * 100.0, 1) if whole else None


class MetricsBuilder:
    def __init__(self, db: Session, business_id: UUID, today: date):
        self.db = db
        self.business_id = business_id
        self.today = today
        self.current, self.previous = periods(today)

    # ---------------------------------------------------------------- per period

    def _revenue(self, p: Period) -> tuple[float, int]:
        row = self.db.execute(
            select(func.sum(Invoice.total_amount), func.count(Invoice.id)).where(
                Invoice.business_id == self.business_id,
                Invoice.is_deleted.is_(False),
                Invoice.status == InvoiceStatus.PAID,
                func.date(Invoice.paid_at) >= p.start,
                func.date(Invoice.paid_at) <= p.end,
            )
        ).one()
        return _money(row[0]), int(row[1] or 0)

    def _expenses(self, p: Period) -> float:
        return _money(self.db.scalar(
            select(func.sum(Expense.amount)).where(
                Expense.business_id == self.business_id,
                Expense.is_deleted.is_(False),
                Expense.direction == TransactionDirection.EXPENSE,
                Expense.transaction_date >= p.start,
                Expense.transaction_date <= p.end,
            )
        ))

    def _appointments(self, p: Period) -> dict:
        status = Appointment.status
        row = self.db.execute(
            select(
                func.count(Appointment.id),
                func.sum(case((status == AppointmentStatus.COMPLETED, 1), else_=0)),
                func.sum(case((status == AppointmentStatus.CANCELLED, 1), else_=0)),
                func.sum(case((status == AppointmentStatus.NO_SHOW, 1), else_=0)),
                func.sum(case((Appointment.notes == ONLINE_NOTE, 1), else_=0)),
            ).where(
                Appointment.business_id == self.business_id,
                Appointment.is_deleted.is_(False),
                Appointment.appointment_date >= p.start,
                Appointment.appointment_date <= p.end,
            )
        ).one()
        total, completed, cancelled, no_show, online = (int(x or 0) for x in row)
        return {
            "total": total,
            "completed": completed,
            "cancelled": cancelled,
            "no_show": no_show,
            "online": online,
            "cancel_rate": _rate(cancelled, total),
            "no_show_rate": _rate(no_show, total),
            "online_share": _rate(online, total),
        }

    def _new_customers(self, p: Period) -> int:
        return int(self.db.scalar(
            select(func.count(Customer.id)).where(
                Customer.business_id == self.business_id,
                Customer.is_deleted.is_(False),
                func.date(Customer.created_at) >= p.start,
                func.date(Customer.created_at) <= p.end,
            )
        ) or 0)

    def _period(self, p: Period) -> dict:
        revenue, paid_invoices = self._revenue(p)
        expenses = self._expenses(p)
        return {
            "start": p.start.isoformat(),
            "end": p.end.isoformat(),
            "revenue": revenue,
            "expenses": expenses,
            "net": round(revenue - expenses, 2),
            "paid_invoices": paid_invoices,
            "average_ticket": round(revenue / paid_invoices, 2) if paid_invoices else None,
            "appointments": self._appointments(p),
            "new_customers": self._new_customers(p),
        }

    # ---------------------------------------------------------------- current only

    def _active(self):
        return (
            Appointment.business_id == self.business_id,
            Appointment.is_deleted.is_(False),
            Appointment.status.notin_((AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW)),
        )

    def _top_services(self) -> list[dict]:
        def counts(p: Period) -> dict:
            rows = self.db.execute(
                select(Service.name, func.count(Appointment.id))
                .join(Service, Service.id == Appointment.service_id)
                .where(*self._active(), Appointment.appointment_date >= p.start, Appointment.appointment_date <= p.end)
                .group_by(Service.id, Service.name)
            ).all()
            return {name: int(n) for name, n in rows}

        current, previous = counts(self.current), counts(self.previous)
        top = sorted(current.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        return [
            {"service": name, "appointments": n, "previous_appointments": previous.get(name, 0),
             "change_pct": pct_change(n, previous.get(name, 0))}
            for name, n in top
        ]

    def _weekdays(self) -> dict:
        rows = self.db.execute(
            select(extract("isodow", Appointment.appointment_date).label("dow"), func.count(Appointment.id))
            .where(*self._active(), Appointment.appointment_date >= self.current.start,
                   Appointment.appointment_date <= self.current.end)
            .group_by("dow")
        ).all()
        by_day = {int(d) - 1: int(n) for d, n in rows}
        if not by_day:
            return {}
        busiest = max(by_day.items(), key=lambda kv: (kv[1], -kv[0]))
        quietest = min(((d, by_day.get(d, 0)) for d in range(7)), key=lambda kv: (kv[1], kv[0]))
        return {
            "busiest_weekday": WEEKDAYS_TR[busiest[0]], "busiest_weekday_appointments": busiest[1],
            "quietest_weekday": WEEKDAYS_TR[quietest[0]], "quietest_weekday_appointments": quietest[1],
        }

    def _busiest_hour(self) -> dict:
        row = self.db.execute(
            select(extract("hour", Appointment.start_time).label("h"), func.count(Appointment.id).label("n"))
            .where(*self._active(), Appointment.appointment_date >= self.current.start,
                   Appointment.appointment_date <= self.current.end)
            .group_by("h").order_by(func.count(Appointment.id).desc(), "h").limit(1)
        ).first()
        return {"busiest_hour": f"{int(row.h):02d}:00", "busiest_hour_appointments": int(row.n)} if row else {}

    def _staff_anonymous(self) -> list[dict]:
        """Per-staff load and cancellations WITHOUT names: 'Personel A', 'Personel B', ..."""
        rows = self.db.execute(
            select(
                Appointment.staff_id,
                func.count(Appointment.id),
                func.sum(case((Appointment.status == AppointmentStatus.CANCELLED, 1), else_=0)),
            )
            .where(
                Appointment.business_id == self.business_id,
                Appointment.is_deleted.is_(False),
                Appointment.staff_id.isnot(None),
                Appointment.appointment_date >= self.current.start,
                Appointment.appointment_date <= self.current.end,
            )
            .group_by(Appointment.staff_id)
        ).all()
        stats = sorted(((int(total), int(cancelled or 0)) for _, total, cancelled in rows), key=lambda x: -x[0])
        if len(stats) < 2:
            return []  # a single person would be identifiable
        return [
            {"label": f"Personel {chr(65 + i)}", "appointments": total, "cancel_rate": _rate(cancelled, total)}
            for i, (total, cancelled) in enumerate(stats[:6])
        ]

    def _upcoming_and_pending(self) -> dict:
        upcoming = self.db.scalar(
            select(func.count(Appointment.id)).where(
                *self._active(),
                Appointment.appointment_date > self.today,
                Appointment.appointment_date <= self.today + timedelta(days=7),
            )
        )
        pending_appointments = self.db.scalar(
            select(func.count(Appointment.id)).where(
                Appointment.business_id == self.business_id,
                Appointment.is_deleted.is_(False),
                Appointment.status == AppointmentStatus.PENDING,
                Appointment.appointment_date >= self.today,
            )
        )
        pending_actions = self.db.scalar(
            select(func.count(AgentAction.id)).where(
                AgentAction.business_id == self.business_id,
                AgentAction.status == "PENDING",
                AgentAction.is_deleted.is_(False),
            )
        )
        return {
            "upcoming_7_days": int(upcoming or 0),
            "pending_appointment_approvals": int(pending_appointments or 0),
            "pending_agent_drafts": int(pending_actions or 0),
        }

    # ---------------------------------------------------------------- public

    def appointments_last_60_days(self) -> int:
        return int(self.db.scalar(
            select(func.count(Appointment.id)).where(
                Appointment.business_id == self.business_id,
                Appointment.is_deleted.is_(False),
                Appointment.appointment_date >= self.previous.start,
                Appointment.appointment_date <= self.today,
            )
        ) or 0)

    def build(self) -> dict:
        cur, prev = self._period(self.current), self._period(self.previous)
        ca, pa = cur["appointments"], prev["appointments"]
        changes = {
            "revenue_pct": pct_change(cur["revenue"], prev["revenue"]),
            "expenses_pct": pct_change(cur["expenses"], prev["expenses"]),
            "net_pct": pct_change(cur["net"], prev["net"]) if prev["net"] > 0 else None,
            "appointments_pct": pct_change(ca["total"], pa["total"]),
            "completed_pct": pct_change(ca["completed"], pa["completed"]),
            "cancelled_pct": pct_change(ca["cancelled"], pa["cancelled"]),
            "new_customers_pct": pct_change(cur["new_customers"], prev["new_customers"]),
            "average_ticket_pct": (pct_change(cur["average_ticket"], prev["average_ticket"])
                                   if cur["average_ticket"] and prev["average_ticket"] else None),
            # rates: difference in percentage points, not percent of percent
            "cancel_rate_pp": (round(ca["cancel_rate"] - pa["cancel_rate"], 1)
                               if ca["cancel_rate"] is not None and pa["cancel_rate"] is not None else None),
        }
        return {
            "currency": "TRY",
            "period_days": PERIOD_DAYS,
            "today": self.today.isoformat(),
            "current": cur,
            "previous": prev,
            "changes": changes,
            "top_services": self._top_services(),
            **self._weekdays(),
            **self._busiest_hour(),
            "staff": self._staff_anonymous(),
            **self._upcoming_and_pending(),
        }


def build_metrics(db: Session, business_id: UUID, today: date) -> dict:
    return MetricsBuilder(db, business_id, today).build()


def has_enough_data(db: Session, business_id: UUID, today: date) -> tuple[bool, int, float]:
    """(enough, appointments in last 60 days, revenue in last 60 days)."""
    builder = MetricsBuilder(db, business_id, today)
    appointments = builder.appointments_last_60_days()
    revenue = builder._revenue(Period(builder.previous.start, today))[0]
    return appointments >= MIN_APPOINTMENTS_60D or revenue > 0, appointments, revenue


__all__ = ["build_metrics", "has_enough_data", "periods", "pct_change", "MIN_APPOINTMENTS_60D"]
