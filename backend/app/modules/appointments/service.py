from __future__ import annotations

from datetime import date, datetime, time, timedelta
from uuid import UUID

from app.core.exceptions import NotFoundException
from app.db.unit_of_work import UnitOfWork
from app.modules.appointments.models import Appointment
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
)
from app.shared.enums.appointment import AppointmentStatus


class AppointmentService:

    def __init__(
        self,
        repository: AppointmentRepository,
        uow: UnitOfWork,
        schedule_block_repo = None,
    ):
        self.repository = repository
        self.uow = uow
        self.schedule_block_repo = schedule_block_repo

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    def create(
        self,
        business_id: UUID,
        data: AppointmentCreate,
    ) -> Appointment:

        appointment = Appointment(
            business_id=business_id,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            customer_email=data.customer_email,
            customer_id=data.customer_id,
            service_id=data.service_id,
            staff_id=data.staff_id,
            branch_id=data.branch_id,
            appointment_date=data.appointment_date,
            start_time=data.start_time,
            end_time=data.end_time,
            notes=data.notes,
        )

        with self.uow:

            self.repository.create(
                appointment,
            )

            self.uow.flush()

            self.uow.refresh(
                appointment,
            )

        return appointment

    # --------------------------------------------------
    # LIST
    # --------------------------------------------------

    def list(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Appointment]:

        return self.repository.list_by_business(
            business_id,
            page=page,
            size=size,
        )

    # --------------------------------------------------
    # GET
    # --------------------------------------------------

    def get(
        self,
        business_id: UUID,
        appointment_id: UUID,
    ) -> Appointment:

        appointment = self.repository.get_by_business(
            business_id,
            appointment_id,
        )

        if appointment is None:

            raise NotFoundException(
                "Appointment not found.",
            )

        return appointment

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update(
        self,
        business_id: UUID,
        appointment_id: UUID,
        data: AppointmentUpdate,
    ) -> Appointment:

        appointment = self.get(
            business_id,
            appointment_id,
        )

        update_data = data.model_dump(
            exclude_unset=True,
        )

        for key, value in update_data.items():
            setattr(
                appointment,
                key,
                value,
            )

        with self.uow:

            self.uow.flush()

            self.uow.refresh(
                appointment,
            )

        return appointment

    # --------------------------------------------------
    # CANCEL
    # --------------------------------------------------

    def cancel(
        self,
        business_id: UUID,
        appointment_id: UUID,
    ) -> Appointment:

        appointment = self.get(
            business_id,
            appointment_id,
        )

        appointment.status = AppointmentStatus.CANCELLED

        with self.uow:

            self.uow.flush()

            self.uow.refresh(
                appointment,
            )

        return appointment

    # --------------------------------------------------
    # COMPLETE
    # --------------------------------------------------

    def complete(
        self,
        business_id: UUID,
        appointment_id: UUID,
    ) -> Appointment:

        appointment = self.get(
            business_id,
            appointment_id,
        )

        appointment.status = AppointmentStatus.COMPLETED

        with self.uow:

            self.uow.flush()

            self.uow.refresh(
                appointment,
            )

        return appointment

    # --------------------------------------------------
    # LIST BY DATE
    # --------------------------------------------------

    def list_by_date(
        self,
        business_id: UUID,
        target_date: date,
    ) -> list[Appointment]:

        return self.repository.list_by_date(
            business_id,
            target_date,
        )

    # --------------------------------------------------
    # AVAILABLE SLOTS
    # --------------------------------------------------

    def get_available_slots(
        self,
        business_id: UUID,
        target_date: date,
        duration_minutes: int = 60,
        staff_id: UUID | None = None,
        branch_id: UUID | None = None,
    ) -> list[str]:
        """
        Returns available time slots for a date.
        Working hours: 09:00-18:00.
        Checks existing appointments and schedule blocks.
        """

        if staff_id:
            appointments = self.repository.list_by_staff(business_id, staff_id, target_date)
        elif branch_id:
            appointments = self.repository.list_by_branch(business_id, branch_id, target_date)
        else:
            appointments = self.repository.list_by_date(
                business_id,
                target_date,
            )

        # Build booked ranges
        booked_ranges = []

        for appt in appointments:
            if appt.status in (
                AppointmentStatus.CANCELLED,
                AppointmentStatus.NO_SHOW,
            ):
                continue

            start = datetime.combine(
                target_date, appt.start_time,
            )

            end_t = appt.end_time or (
                start + timedelta(minutes=60)
            ).time()

            end = datetime.combine(
                target_date, end_t,
            )

            booked_ranges.append((start, end))
            
        if self.schedule_block_repo:
            blocks = self.schedule_block_repo.list_active_blocks_for_date(business_id, target_date)
            from app.shared.enums.schedule_block import BlockType
            for block in blocks:
                if block.block_type == BlockType.FULL_DAY:
                    booked_ranges.append((
                        datetime.combine(target_date, time(0, 0)),
                        datetime.combine(target_date, time(23, 59, 59))
                    ))
                elif block.block_type in (BlockType.TIME_RANGE, BlockType.RECURRING):
                    st = block.start_time or time(0, 0)
                    et = block.end_time or time(23, 59, 59)
                    booked_ranges.append((
                        datetime.combine(target_date, st),
                        datetime.combine(target_date, et)
                    ))

        # Generate available slots
        available = []

        current = datetime.combine(
            target_date,
            time(9, 0),
        )

        end_of_day = datetime.combine(
            target_date,
            time(18, 0),
        )

        while current + timedelta(minutes=duration_minutes) <= end_of_day:

            slot_end = current + timedelta(
                minutes=duration_minutes,
            )

            conflict = False
            for booked_start, booked_end in booked_ranges:
                if current < booked_end and slot_end > booked_start:
                    conflict = True
                    break

            if not conflict:
                available.append(
                    current.strftime("%H:%M")
                )

            current += timedelta(minutes=30)

        return available
