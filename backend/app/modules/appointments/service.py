from __future__ import annotations

from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from app.core.config import settings

from app.core.exceptions import NotFoundException
from app.db.unit_of_work import UnitOfWork
from app.modules.appointments.models import Appointment
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
)
from app.shared.enums.appointment import AppointmentStatus


def local_now() -> datetime:
    """Current wall-clock time in APP_TIMEZONE (naive, like appointment times)."""
    return datetime.now(ZoneInfo(settings.APP_TIMEZONE)).replace(tzinfo=None)


class AppointmentService:

    def __init__(
        self,
        repository: AppointmentRepository,
        uow: UnitOfWork,
        schedule_block_repo = None,
        business_hours_service = None,
        staff_schedule_repo = None,
        staff_profile_repo = None,
        now_fn = None,
    ):
        self.repository = repository
        # Injectable clock so slot tests do not depend on the real date.
        self.now_fn = now_fn or local_now
        self.uow = uow
        self.schedule_block_repo = schedule_block_repo
        self.business_hours_service = business_hours_service
        self.staff_schedule_repo = staff_schedule_repo
        self.staff_profile_repo = staff_profile_repo

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

    def _get_opening_window(
        self,
        business_id: UUID,
        target_date: date,
        branch_id: UUID | None,
    ) -> tuple[time, time] | None:
        """Business/branch hours for the day, or None if closed."""

        if self.business_hours_service is None:
            # Fallback when the service is built without business hours.
            from app.modules.business_hours.service import (
                DEFAULT_CLOSE_TIME,
                DEFAULT_OPEN_TIME,
            )
            return DEFAULT_OPEN_TIME, DEFAULT_CLOSE_TIME

        return self.business_hours_service.get_open_window(
            business_id, target_date, branch_id,
        )

    def _intersect_staff_hours(
        self,
        staff_id: UUID,
        target_date: date,
        open_time: time,
        close_time: time,
    ) -> tuple[time, time] | None:
        """
        Narrows the opening window to the staff member's working hours.

        - Staff without any schedule rows: no restriction.
        - Staff with a schedule but no (working) row for this weekday: not available.
        """

        if self.staff_schedule_repo is None:
            return open_time, close_time

        schedule = self.staff_schedule_repo.get_schedule_for_staff(staff_id)
        if not schedule:
            return open_time, close_time

        day = next(
            (s for s in schedule if s.day_of_week == target_date.weekday()),
            None,
        )
        if day is None or not day.is_working:
            return None

        start = max(open_time, day.start_time)
        end = min(close_time, day.end_time)
        if start >= end:
            return None
        return start, end

    def get_available_slots(
        self,
        business_id: UUID,
        target_date: date,
        duration_minutes: int = 60,
        staff_id: UUID | None = None,
        branch_id: UUID | None = None,
    ) -> list[str]:
        """
        Returns available time slots ("HH:MM") for a date.

        1. Opening window from business_hours (branch week > business week > 09:00-18:00 default).
        2. If a staff member is given, intersected with their staff_schedules for that weekday.
        3. Schedule blocks (business-wide + this branch) and existing appointments are removed.
        4. Past days have no slots; for today only slots starting after "now" are offered.
        """

        now = self.now_fn()
        if target_date < now.date():
            return []
        not_before = now if target_date == now.date() else None

        # A staff member works at one branch; use it when no branch was given.
        if staff_id and branch_id is None and self.staff_profile_repo:
            staff = self.staff_profile_repo.get_by_business(business_id, staff_id)
            if staff is not None:
                branch_id = staff.branch_id

        window = self._get_opening_window(business_id, target_date, branch_id)
        if window is None:
            return []

        if staff_id:
            window = self._intersect_staff_hours(staff_id, target_date, *window)
            if window is None:
                return []

        open_time, close_time = window

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
            blocks = self.schedule_block_repo.list_active_blocks_for_date(
                business_id, target_date, branch_id,
            )
            from app.shared.enums.schedule_block import BlockType
            for block in blocks:
                if block.block_type == BlockType.FULL_DAY:
                    return []
                elif block.block_type in (BlockType.TIME_RANGE, BlockType.RECURRING):
                    st = block.start_time or time(0, 0)
                    et = block.end_time or time(23, 59, 59)
                    booked_ranges.append((
                        datetime.combine(target_date, st),
                        datetime.combine(target_date, et)
                    ))

        # Generate available slots inside the opening window
        available = []

        current = datetime.combine(
            target_date,
            open_time,
        )

        end_of_day = datetime.combine(
            target_date,
            close_time,
        )

        while current + timedelta(minutes=duration_minutes) <= end_of_day:

            slot_end = current + timedelta(
                minutes=duration_minutes,
            )

            if not_before is not None and current <= not_before:
                current += timedelta(minutes=30)
                continue

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
