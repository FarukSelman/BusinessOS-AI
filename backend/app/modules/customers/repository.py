from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import case, select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base_repository import BaseRepository
from app.modules.appointments.models import Appointment
from app.modules.customers.models import Customer
from app.shared.enums.appointment import AppointmentStatus
from app.shared.utils.search import count_rows, text_search


def _local_midnight(day: date) -> datetime:
    """Start of a calendar day in APP_TIMEZONE, as an aware datetime."""
    return datetime.combine(day, time.min, tzinfo=ZoneInfo(settings.APP_TIMEZONE))


class CustomerRepository(
    BaseRepository[Customer]
):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Customer,
        )


    def list_by_business(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Customer]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.created_at.desc(),
                self.model.id.asc(),  # sayfalama kararlı olsun
            )
            .offset(
                (page - 1) * size
            )
            .limit(size)
        )

        return list(
            self.db.scalars(statement).all()
        )


    def get_by_business(
        self,
        business_id: UUID,
        customer_id: UUID,
    ) -> Customer | None:

        statement = (
            select(self.model)
            .where(
                self.model.id == customer_id,
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)


    def get_by_phone(
        self,
        business_id: UUID,
        phone: str,
    ) -> Customer | None:
        """Matches on digits only, so '0532 111 22 33' and '05321112233' are the same customer."""

        digits = "".join(ch for ch in phone if ch.isdigit())
        if not digits:
            return None

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
                func.regexp_replace(self.model.phone, r"\D", "", "g") == digits,
            )
            .order_by(self.model.created_at)
            .limit(1)
        )

        return self.db.scalar(statement)


    def search_by_name(
        self,
        business_id: UUID,
        query: str,
    ) -> list[Customer]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.name.ilike(f"%{query}%"),
                self.model.is_deleted.is_(False),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )


    def count_by_business(
        self,
        business_id: UUID,
    ) -> int:

        statement = (
            select(func.count())
            .select_from(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement) or 0

    def list_by_business_filtered(
        self,
        business_id: UUID,
        tag_ids: list[UUID] | None = None,
        status: str | None = None,
        min_visits: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Customer], int]:
        """One page of customers and the total matching the filters."""
        from app.modules.customer_tags.models import CustomerTagAssignment

        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )

        condition = text_search(search, self.model.name, self.model.email, phone_columns=(self.model.phone,))
        if condition is not None:
            statement = statement.where(condition)

        if tag_ids:
            for tag_id in tag_ids:
                statement = statement.where(
                    self.model.id.in_(
                        select(CustomerTagAssignment.customer_id).where(
                            CustomerTagAssignment.tag_id == tag_id,
                            CustomerTagAssignment.is_deleted.is_(False)
                        )
                    )
                )

        if status:
            statement = statement.where(self.model.status == status)

        # At least N completed appointments
        if min_visits and min_visits > 0:
            statement = statement.where(
                self.model.id.in_(
                    select(Appointment.customer_id)
                    .where(
                        Appointment.business_id == business_id,
                        Appointment.status == AppointmentStatus.COMPLETED,
                        Appointment.is_deleted.is_(False),
                    )
                    .group_by(Appointment.customer_id)
                    .having(func.count() >= min_visits)
                )
            )

        # Whole local days: date_to includes customers created on that day.
        if date_from:
            statement = statement.where(self.model.created_at >= _local_midnight(date_from))
        if date_to:
            statement = statement.where(self.model.created_at < _local_midnight(date_to + timedelta(days=1)))

        total = count_rows(self.db, statement)
        statement = statement.order_by(self.model.created_at.desc(), self.model.id.asc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all()), total

    def tags_by_customer(self, customer_ids: list[UUID]) -> dict[UUID, list]:
        """Tags of many customers in one query (no request per customer)."""
        from app.modules.customer_tags.models import CustomerTag, CustomerTagAssignment

        result: dict[UUID, list] = {cid: [] for cid in customer_ids}
        if not customer_ids:
            return result
        rows = self.db.execute(
            select(CustomerTagAssignment.customer_id, CustomerTag)
            .join(CustomerTag, CustomerTag.id == CustomerTagAssignment.tag_id)
            .where(
                CustomerTagAssignment.customer_id.in_(customer_ids),
                CustomerTagAssignment.is_deleted.is_(False),
                CustomerTag.is_deleted.is_(False),
            )
            .order_by(CustomerTag.name)
        ).all()
        for customer_id, tag in rows:
            result[customer_id].append(tag)
        return result

    def visit_stats(self, business_id: UUID, customer_ids: list[UUID]) -> dict[UUID, dict]:
        """Completed visits and last visit of many customers in one query.

        Last visit: the latest appointment that was not cancelled and is not in
        the future (today counts), so an upcoming booking is not a "visit".
        """
        result: dict[UUID, dict] = {cid: {"completed_visits": 0, "last_visit_date": None} for cid in customer_ids}
        if not customer_ids:
            return result
        today = datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date()
        rows = self.db.execute(
            select(
                Appointment.customer_id,
                func.count().filter(Appointment.status == AppointmentStatus.COMPLETED),
                func.max(
                    case(
                        (
                            (Appointment.status != AppointmentStatus.CANCELLED) & (Appointment.appointment_date <= today),
                            Appointment.appointment_date,
                        )
                    )
                ),
            )
            .where(
                Appointment.business_id == business_id,
                Appointment.customer_id.in_(customer_ids),
                Appointment.is_deleted.is_(False),
            )
            .group_by(Appointment.customer_id)
        ).all()
        for customer_id, completed, last_visit in rows:
            result[customer_id] = {"completed_visits": completed, "last_visit_date": last_visit}
        return result
