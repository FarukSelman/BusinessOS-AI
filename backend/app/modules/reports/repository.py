import uuid
from datetime import date, datetime
from sqlalchemy import select, func, case, extract, and_
from sqlalchemy.orm import Session

from app.modules.customers.models import Customer
from app.modules.appointments.models import Appointment
from app.modules.invoice.models import Invoice
from app.modules.expenses.models import Expense
from app.modules.services.models import Service
from app.modules.staff.models import StaffProfile
from app.modules.branches.models import Branch

from app.shared.enums.invoice import InvoiceStatus
from app.shared.enums.expense import TransactionDirection
from app.shared.enums.appointment import AppointmentStatus

class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self, business_id: uuid.UUID, today: date, month_start: date) -> dict:
        # total_customers
        total_customers = self.db.scalar(
            select(func.count(Customer.id))
            .where(Customer.business_id == business_id, Customer.is_deleted.is_(False))
        ) or 0

        # total_appointments_today
        total_appointments_today = self.db.scalar(
            select(func.count(Appointment.id))
            .where(
                Appointment.business_id == business_id,
                Appointment.is_deleted.is_(False),
                Appointment.appointment_date == today
            )
        ) or 0

        # total_appointments_this_month
        total_appointments_this_month = self.db.scalar(
            select(func.count(Appointment.id))
            .where(
                Appointment.business_id == business_id,
                Appointment.is_deleted.is_(False),
                Appointment.appointment_date >= month_start
            )
        ) or 0

        # total_revenue_this_month
        total_revenue_this_month = self.db.scalar(
            select(func.sum(Invoice.total_amount))
            .where(
                Invoice.business_id == business_id,
                Invoice.is_deleted.is_(False),
                Invoice.status == InvoiceStatus.PAID,
                func.date(Invoice.paid_at) >= month_start
            )
        ) or 0.0

        # total_expenses_this_month
        total_expenses_this_month = self.db.scalar(
            select(func.sum(Expense.amount))
            .where(
                Expense.business_id == business_id,
                Expense.is_deleted.is_(False),
                Expense.direction == TransactionDirection.EXPENSE,
                Expense.transaction_date >= month_start
            )
        ) or 0.0

        # net_profit_this_month
        net_profit_this_month = float(total_revenue_this_month) - float(total_expenses_this_month)

        # pending_appointments
        pending_appointments = self.db.scalar(
            select(func.count(Appointment.id))
            .where(
                Appointment.business_id == business_id,
                Appointment.is_deleted.is_(False),
                Appointment.status == AppointmentStatus.PENDING
            )
        ) or 0

        # active_staff_count
        active_staff_count = self.db.scalar(
            select(func.count(StaffProfile.id))
            .where(StaffProfile.business_id == business_id, StaffProfile.is_deleted.is_(False))
        ) or 0

        return {
            "total_customers": total_customers,
            "total_appointments_today": total_appointments_today,
            "total_appointments_this_month": total_appointments_this_month,
            "total_revenue_this_month": float(total_revenue_this_month),
            "total_expenses_this_month": float(total_expenses_this_month),
            "net_profit_this_month": float(net_profit_this_month),
            "pending_appointments": pending_appointments,
            "active_staff_count": active_staff_count,
        }

    def get_revenue_report(self, business_id: uuid.UUID, start_date: date, end_date: date, group_by: str) -> list[dict]:
        # group_by 'daily', 'weekly', 'monthly'
        if group_by == 'monthly':
            trunc_str = 'month'
        elif group_by == 'weekly':
            trunc_str = 'week'
        else:
            trunc_str = 'day'

        # Income query
        income_query = (
            select(
                func.date_trunc(trunc_str, Invoice.paid_at).label('period'),
                func.sum(Invoice.total_amount).label('income'),
                func.count(Invoice.id).label('invoice_count')
            )
            .where(
                Invoice.business_id == business_id,
                Invoice.is_deleted.is_(False),
                Invoice.status == InvoiceStatus.PAID,
                func.date(Invoice.paid_at) >= start_date,
                func.date(Invoice.paid_at) <= end_date
            )
            .group_by('period')
            .subquery()
        )

        # Expense query
        expense_query = (
            select(
                func.date_trunc(trunc_str, Expense.transaction_date).label('period'),
                func.sum(Expense.amount).label('expense')
            )
            .where(
                Expense.business_id == business_id,
                Expense.is_deleted.is_(False),
                Expense.direction == TransactionDirection.EXPENSE,
                Expense.transaction_date >= start_date,
                Expense.transaction_date <= end_date
            )
            .group_by('period')
            .subquery()
        )

        # We can simulate FULL OUTER JOIN by getting all periods in Python or combine them.
        # Given potential complexity with SQLAlchemy outer joins, let's fetch both and combine in memory for simplicity.
        incomes = self.db.execute(select(income_query.c.period, income_query.c.income, income_query.c.invoice_count)).all()
        expenses = self.db.execute(select(expense_query.c.period, expense_query.c.expense)).all()

        combined = {}
        for period, income, count in incomes:
            if period:
                p_str = str(period.date()) if isinstance(period, datetime) else str(period)
                combined[p_str] = {"period": p_str, "income": float(income or 0), "expense": 0.0, "net": float(income or 0), "invoice_count": count or 0}

        for period, expense in expenses:
            if period:
                p_str = str(period.date()) if isinstance(period, datetime) else str(period)
                if p_str not in combined:
                    combined[p_str] = {"period": p_str, "income": 0.0, "expense": float(expense or 0), "net": -float(expense or 0), "invoice_count": 0}
                else:
                    combined[p_str]["expense"] = float(expense or 0)
                    combined[p_str]["net"] = combined[p_str]["income"] - combined[p_str]["expense"]

        return list(combined.values())

    def get_appointment_report(self, business_id: uuid.UUID, start_date: date, end_date: date) -> dict:
        apps = self.db.scalars(
            select(Appointment)
            .where(
                Appointment.business_id == business_id,
                Appointment.is_deleted.is_(False),
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date
            )
        ).all()

        total = len(apps)
        completed = sum(1 for a in apps if a.status == AppointmentStatus.COMPLETED)
        cancelled = sum(1 for a in apps if a.status == AppointmentStatus.CANCELLED)
        no_show = sum(1 for a in apps if a.status == AppointmentStatus.NO_SHOW)

        completion_rate = (completed / total * 100.0) if total > 0 else 0.0

        return {
            "total_appointments": total,
            "completed_count": completed,
            "cancelled_count": cancelled,
            "no_show_count": no_show,
            "completion_rate": completion_rate,
        }

    def get_appointments_by_service(self, business_id: uuid.UUID, start_date: date, end_date: date) -> list[dict]:
        stmt = (
            select(Service.name, func.count(Appointment.id).label('count'), func.sum(Invoice.total_amount).label('revenue'))
            .outerjoin(Appointment, and_(Appointment.service_id == Service.id, Appointment.appointment_date >= start_date, Appointment.appointment_date <= end_date, Appointment.is_deleted.is_(False)))
            .outerjoin(Invoice, and_(Invoice.appointment_id == Appointment.id, Invoice.status == InvoiceStatus.PAID, Invoice.is_deleted.is_(False)))
            .where(Service.business_id == business_id, Service.is_deleted.is_(False))
            .group_by(Service.id)
        )
        res = self.db.execute(stmt).all()
        return [{"service_name": r.name, "count": r.count or 0, "revenue": float(r.revenue or 0)} for r in res]

    def get_customer_report(self, business_id: uuid.UUID, start_date: date, end_date: date) -> dict:
        new_count = self.db.scalar(
            select(func.count(Customer.id))
            .where(
                Customer.business_id == business_id,
                Customer.is_deleted.is_(False),
                func.date(Customer.created_at) >= start_date,
                func.date(Customer.created_at) <= end_date
            )
        ) or 0

        # returning customers (customers with >1 completed appointments)
        subq = (
            select(Appointment.customer_id, func.count(Appointment.id).label("c"))
            .where(Appointment.business_id == business_id, Appointment.is_deleted.is_(False))
            .group_by(Appointment.customer_id)
            .subquery()
        )
        returning_count = self.db.scalar(
            select(func.count(Customer.id))
            .join(subq, Customer.id == subq.c.customer_id)
            .where(Customer.business_id == business_id, Customer.is_deleted.is_(False), subq.c.c > 1)
        ) or 0

        return {
            "new_customers_count": new_count,
            "returning_customers_count": returning_count,
        }

    def get_top_customers(self, business_id: uuid.UUID) -> list[dict]:
        stmt = (
            select(Customer.name, func.count(Appointment.id).label('visit_count'), func.sum(Invoice.total_amount).label('total_spent'))
            .outerjoin(Appointment, and_(Appointment.customer_id == Customer.id, Appointment.is_deleted.is_(False)))
            .outerjoin(Invoice, and_(Invoice.customer_id == Customer.id, Invoice.status == InvoiceStatus.PAID, Invoice.is_deleted.is_(False)))
            .where(Customer.business_id == business_id, Customer.is_deleted.is_(False))
            .group_by(Customer.id)
            .order_by(func.sum(Invoice.total_amount).desc().nulls_last())
            .limit(10)
        )
        res = self.db.execute(stmt).all()
        return [{"name": r.name, "visit_count": r.visit_count or 0, "total_spent": float(r.total_spent or 0)} for r in res]

    def get_customer_growth(self, business_id: uuid.UUID, start_date: date, end_date: date) -> list[dict]:
        stmt = (
            select(func.date_trunc('month', Customer.created_at).label('month'), func.count(Customer.id).label('count'))
            .where(Customer.business_id == business_id, Customer.is_deleted.is_(False), func.date(Customer.created_at) >= start_date, func.date(Customer.created_at) <= end_date)
            .group_by('month')
            .order_by('month')
        )
        res = self.db.execute(stmt).all()
        return [{"month": str(r.month.date()) if r.month else "", "count": r.count} for r in res]

    def get_service_stats(self, business_id: uuid.UUID, start_date: date, end_date: date) -> list[dict]:
        stmt = (
            select(Service.name, func.count(Appointment.id).label('booking_count'), func.sum(Invoice.total_amount).label('revenue'))
            .outerjoin(Appointment, and_(Appointment.service_id == Service.id, Appointment.appointment_date >= start_date, Appointment.appointment_date <= end_date, Appointment.is_deleted.is_(False)))
            .outerjoin(Invoice, and_(Invoice.appointment_id == Appointment.id, Invoice.status == InvoiceStatus.PAID, Invoice.is_deleted.is_(False)))
            .where(Service.business_id == business_id, Service.is_deleted.is_(False))
            .group_by(Service.id)
            .order_by(func.count(Appointment.id).desc().nulls_last())
        )
        res = self.db.execute(stmt).all()
        return [{"name": r.name, "booking_count": r.booking_count or 0, "revenue": float(r.revenue or 0), "avg_rating": None} for r in res]

    def get_staff_performance(self, business_id: uuid.UUID, start_date: date, end_date: date) -> list[dict]:
        stmt = (
            select(
                StaffProfile.full_name,
                StaffProfile.title,
                func.count(Appointment.id).label('app_count'),
                func.sum(case((Appointment.status == AppointmentStatus.COMPLETED, 1), else_=0)).label('completed_count'),
                func.sum(Invoice.total_amount).label('revenue')
            )
            .outerjoin(Appointment, and_(Appointment.staff_id == StaffProfile.id, Appointment.appointment_date >= start_date, Appointment.appointment_date <= end_date, Appointment.is_deleted.is_(False)))
            .outerjoin(Invoice, and_(Invoice.appointment_id == Appointment.id, Invoice.status == InvoiceStatus.PAID, Invoice.is_deleted.is_(False)))
            .where(StaffProfile.business_id == business_id, StaffProfile.is_deleted.is_(False))
            .group_by(StaffProfile.id)
        )
        res = self.db.execute(stmt).all()
        out = []
        for r in res:
            ac = r.app_count or 0
            cc = r.completed_count or 0
            cr = (cc / ac * 100.0) if ac > 0 else 0.0
            out.append({
                "name": r.full_name,
                "title": r.title,
                "appointment_count": ac,
                "revenue": float(r.revenue or 0),
                "completion_rate": cr
            })
        return out
