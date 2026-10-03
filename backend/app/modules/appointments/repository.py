from datetime import date
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository
from app.modules.appointments.models import Appointment
from app.shared.enums.appointment import AppointmentStatus


class AppointmentRepository(
    BaseRepository[Appointment]
):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Appointment,
        )

    def list_by_business(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Appointment]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.appointment_date.desc(),
                self.model.start_time.asc(),
            )
            .offset(
                (page - 1) * size,
            )
            .limit(size)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_by_business(
        self,
        business_id: UUID,
        appointment_id: UUID,
    ) -> Appointment | None:

        statement = (
            select(self.model)
            .where(
                self.model.id == appointment_id,
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    def list_by_date(
        self,
        business_id: UUID,
        target_date: date,
    ) -> list[Appointment]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.appointment_date == target_date,
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.start_time.asc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def list_by_customer(
        self,
        business_id: UUID,
        customer_id: UUID,
    ) -> list[Appointment]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.customer_id == customer_id,
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.appointment_date.desc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def list_by_status(
        self,
        business_id: UUID,
        status: AppointmentStatus,
    ) -> list[Appointment]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.status == status,
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.appointment_date.desc(),
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
            select(
                func.count(self.model.id)
            )
            .where(
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement) or 0

    def count_by_date_range(
        self,
        business_id: UUID,
        start_date: date,
        end_date: date,
    ) -> int:

        statement = (
            select(
                func.count(self.model.id)
            )
            .where(
                self.model.business_id == business_id,
                self.model.appointment_date >= start_date,
                self.model.appointment_date <= end_date,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement) or 0

    def list_by_staff(
        self,
        business_id: UUID,
        staff_id: UUID,
        target_date: date | None = None,
    ) -> list[Appointment]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.staff_id == staff_id,
            self.model.is_deleted.is_(False),
        )
        if target_date:
            statement = statement.where(self.model.appointment_date == target_date)
            
        statement = statement.order_by(self.model.appointment_date.desc(), self.model.start_time.asc())
        return list(self.db.scalars(statement).all())

    def list_by_branch(
        self,
        business_id: UUID,
        branch_id: UUID,
        target_date: date | None = None,
    ) -> list[Appointment]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.branch_id == branch_id,
            self.model.is_deleted.is_(False),
        )
        if target_date:
            statement = statement.where(self.model.appointment_date == target_date)
            
        statement = statement.order_by(self.model.appointment_date.desc(), self.model.start_time.asc())
        return list(self.db.scalars(statement).all())
