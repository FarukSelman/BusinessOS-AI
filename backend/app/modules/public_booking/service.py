"""
Public (no login) online booking.

Safety rules
- Only ACTIVE, non-deleted businesses, active branches, active services and
  active staff who actually offer the service are visible or bookable.
- A booking runs in ONE transaction that first takes a PostgreSQL advisory
  lock for (business, day). While holding it the slot is re-checked, the
  customer found/created and the appointment inserted. Two simultaneous
  requests for the same day are serialised, so the second sees the first
  appointment and gets "saat dolu". (A unique index cannot express
  overlapping intervals of different lengths, the lock can.)
- "Farkı yok" (no staff chosen): a slot is free if at least one eligible staff
  member is free; the booking is assigned to the free one with the fewest
  appointments that day. Businesses without staff who offer the service use
  the business-wide calendar.
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.db.unit_of_work import UnitOfWork
from app.modules.appointments.models import Appointment
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.service import AppointmentService
from app.modules.branches.models import Branch
from app.modules.business.models import Business
from app.modules.business.repository import BusinessRepository
from app.modules.business_hours.models import BusinessHours
from app.modules.customers.models import Customer
from app.modules.customers.repository import CustomerRepository
from app.modules.public_booking.schemas import PublicBookingCreate
from app.modules.services.models import Service
from app.modules.services.repository import ServiceRepository
from app.modules.staff.models import StaffProfile, StaffService
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.business import BusinessStatus
from app.shared.enums.service import ServiceStatus
from app.shared.enums.staff import StaffStatus

PUBLIC_BOOKING_NOTE = "Online randevu sayfasından alındı."
SLOT_TAKEN = "Seçtiğiniz saat artık müsait değil. Lütfen başka bir saat seçin."
DEFAULT_OPEN, DEFAULT_CLOSE = time(9, 0), time(18, 0)  # same default as slot calculation
INACTIVE_APPOINTMENT = (AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW)


@dataclass
class BookingResult:
    appointment: Appointment
    business: Business
    service: Service
    staff: Optional[StaffProfile]
    customer: Customer


class PublicBookingService:
    def __init__(
        self,
        business_repo: BusinessRepository,
        service_repo: ServiceRepository,
        appointment_repo: AppointmentRepository,
        customer_repo: CustomerRepository,
        appointment_service: AppointmentService,
        uow: UnitOfWork,
    ):
        self.business_repo = business_repo
        self.service_repo = service_repo
        self.appointment_repo = appointment_repo
        self.customer_repo = customer_repo
        self.appointment_service = appointment_service
        self.uow = uow

    @property
    def db(self) -> Session:
        return self.appointment_repo.db

    # ------------------------------------------------------------------ lookups

    def get_business_by_slug(self, slug: str) -> Business:
        business = self.business_repo.get_by_slug(slug)
        if not business or business.status != BusinessStatus.ACTIVE:
            raise NotFoundException("İşletme bulunamadı.")
        return business

    def list_public_services(self, business_id: UUID) -> list[Service]:
        return self.service_repo.list_active_by_business(business_id)

    def get_service(self, business_id: UUID, service_id: UUID) -> Service:
        service = self.service_repo.get_by_business(business_id, service_id)
        if not service or service.is_deleted or getattr(service, "status", ServiceStatus.ACTIVE) != ServiceStatus.ACTIVE:
            raise NotFoundException("Hizmet bulunamadı.")
        return service

    def list_branches(self, business_id: UUID) -> list[Branch]:
        return list(self.db.scalars(
            select(Branch)
            .where(Branch.business_id == business_id, Branch.is_deleted.is_(False), Branch.is_active.is_(True))
            .order_by(Branch.is_main.desc(), Branch.name)
        ).all())

    def main_address(self, business_id: UUID) -> Optional[str]:
        for branch in self.list_branches(business_id):
            if branch.address:
                return branch.address
        return None

    def opening_hours(self, business_id: UUID) -> list[dict]:
        """Business-level week; the 09:00-18:00 default when nothing is configured."""
        rows = self.db.scalars(
            select(BusinessHours).where(
                BusinessHours.business_id == business_id,
                BusinessHours.branch_id.is_(None),
                BusinessHours.is_deleted.is_(False),
            )
        ).all()
        if not rows:
            return [{"day_of_week": d, "open_time": DEFAULT_OPEN, "close_time": DEFAULT_CLOSE, "is_closed": False}
                    for d in range(7)]
        by_day = {r.day_of_week: r for r in rows}
        week = []
        for day in range(7):
            row = by_day.get(day)
            if row is None or row.is_closed or not row.open_time or not row.close_time:
                week.append({"day_of_week": day, "open_time": None, "close_time": None, "is_closed": True})
            else:
                week.append({"day_of_week": day, "open_time": row.open_time, "close_time": row.close_time, "is_closed": False})
        return week

    def _check_branch(self, business_id: UUID, branch_id: Optional[UUID]) -> None:
        if branch_id is None:
            return
        branch = self.db.get(Branch, branch_id)
        if branch is None or branch.business_id != business_id or branch.is_deleted or not branch.is_active:
            raise NotFoundException("Şube bulunamadı.")

    def eligible_staff(self, business_id: UUID, service_id: Optional[UUID], branch_id: Optional[UUID]) -> list[StaffProfile]:
        """Active staff of THIS business (offering the service, at this branch or unassigned)."""
        query = select(StaffProfile).where(
            StaffProfile.business_id == business_id,
            StaffProfile.is_deleted.is_(False),
            StaffProfile.status == StaffStatus.ACTIVE,
        )
        if service_id is not None:
            query = query.join(StaffService, StaffService.staff_id == StaffProfile.id).where(
                StaffService.service_id == service_id,
                StaffService.is_deleted.is_(False),
            )
        if branch_id is not None:
            query = query.where((StaffProfile.branch_id == branch_id) | StaffProfile.branch_id.is_(None))
        return list(self.db.scalars(query.order_by(StaffProfile.full_name)).unique().all())

    def staff_services(self, staff_ids: list[UUID]) -> dict[UUID, list[Service]]:
        if not staff_ids:
            return {}
        rows = self.db.execute(
            select(StaffService.staff_id, Service)
            .join(Service, Service.id == StaffService.service_id)
            .where(
                StaffService.staff_id.in_(staff_ids),
                StaffService.is_deleted.is_(False),
                Service.is_deleted.is_(False),
                Service.status == ServiceStatus.ACTIVE,
            )
        ).all()
        result: dict[UUID, list[Service]] = {}
        for staff_id, service in rows:
            result.setdefault(staff_id, []).append(service)
        return result

    def _resolve_staff(self, business_id: UUID, service_id: UUID, branch_id: Optional[UUID],
                       staff_id: Optional[UUID]) -> tuple[Optional[StaffProfile], list[StaffProfile]]:
        """Returns (chosen staff or None, eligible staff for 'farkı yok')."""
        eligible = self.eligible_staff(business_id, service_id, branch_id)
        if staff_id is None:
            return None, eligible
        chosen = next((s for s in eligible if s.id == staff_id), None)
        if chosen is None:
            raise NotFoundException("Seçilen personel bu hizmeti vermiyor.")
        return chosen, eligible

    # ------------------------------------------------------------------ slots

    def _slots_for(self, business_id: UUID, day: date, duration: int, branch_id: Optional[UUID],
                   staff: Optional[StaffProfile], eligible: list[StaffProfile]) -> dict[str, list[StaffProfile]]:
        """'HH:MM' -> staff free at that time ([] means business-wide booking without staff)."""
        if staff is not None:
            return {s: [staff] for s in self.appointment_service.get_available_slots(
                business_id, day, duration_minutes=duration, staff_id=staff.id, branch_id=branch_id)}
        if not eligible:
            return {s: [] for s in self.appointment_service.get_available_slots(
                business_id, day, duration_minutes=duration, branch_id=branch_id)}
        free: dict[str, list[StaffProfile]] = {}
        for member in eligible:
            for slot in self.appointment_service.get_available_slots(
                    business_id, day, duration_minutes=duration, staff_id=member.id, branch_id=branch_id):
                free.setdefault(slot, []).append(member)
        return dict(sorted(free.items()))

    def get_available_slots(self, business_id: UUID, target_date: date, service_id: UUID,
                            staff_id: Optional[UUID] = None, branch_id: Optional[UUID] = None) -> List[time]:
        self._check_branch(business_id, branch_id)
        service = self.get_service(business_id, service_id)
        staff, eligible = self._resolve_staff(business_id, service.id, branch_id, staff_id)
        slots = self._slots_for(business_id, target_date, service.duration_minutes or 30, branch_id, staff, eligible)
        return [datetime.strptime(s, "%H:%M").time() for s in slots]

    # ------------------------------------------------------------------ booking

    def _lock_day(self, business_id: UUID, day: date) -> None:
        """Transaction-scoped lock: released automatically on commit/rollback."""
        self.db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": f"public-booking:{business_id}:{day.isoformat()}"},
        )

    def _least_busy(self, business_id: UUID, day: date, candidates: list[StaffProfile]) -> StaffProfile:
        counts = dict(self.db.execute(
            select(Appointment.staff_id, func.count())
            .where(
                Appointment.business_id == business_id,
                Appointment.appointment_date == day,
                Appointment.staff_id.in_([c.id for c in candidates]),
                Appointment.is_deleted.is_(False),
                Appointment.status.notin_(INACTIVE_APPOINTMENT),
            )
            .group_by(Appointment.staff_id)
        ).all())
        return min(candidates, key=lambda c: (counts.get(c.id, 0), c.full_name))

    def count_open_bookings_for_phone(self, business_id: UUID, phone: str, today: date) -> int:
        digits_phone = func.regexp_replace(Appointment.customer_phone, r"\D", "", "g")
        return self.db.scalar(
            select(func.count()).select_from(Appointment).where(
                Appointment.business_id == business_id,
                Appointment.is_deleted.is_(False),
                Appointment.status == AppointmentStatus.PENDING,
                Appointment.appointment_date >= today,
                digits_phone == phone,
            )
        ) or 0

    def create_public_booking(self, business_slug: str, data: PublicBookingCreate,
                              max_open_per_phone: Optional[int] = None) -> BookingResult:
        if data.website:  # honeypot filled -> bot
            raise BadRequestException("Randevu oluşturulamadı.")

        business = self.get_business_by_slug(business_slug)
        self._check_branch(business.id, data.branch_id)
        service = self.get_service(business.id, data.service_id)
        staff, eligible = self._resolve_staff(business.id, service.id, data.branch_id, data.staff_id)
        duration = service.duration_minutes or 30
        requested = data.start_time.strftime("%H:%M")

        try:
            self._lock_day(business.id, data.date)

            if max_open_per_phone is not None:
                today = self.appointment_service.now_fn().date()
                if self.count_open_bookings_for_phone(business.id, data.customer_phone, today) >= max_open_per_phone:
                    raise ConflictException(
                        "Bu telefon numarasıyla onay bekleyen çok fazla randevu var. "
                        "Lütfen işletmeyle iletişime geçin."
                    )

            free = self._slots_for(business.id, data.date, duration, data.branch_id, staff, eligible)
            if requested not in free:
                raise ConflictException(SLOT_TAKEN)
            if staff is None and free[requested]:
                staff = self._least_busy(business.id, data.date, free[requested])

            customer = self.customer_repo.get_by_phone(business.id, data.customer_phone)
            if customer is None:
                customer = Customer(
                    business_id=business.id,
                    name=data.customer_name,
                    phone=data.customer_phone,
                    email=data.customer_email,
                )
                self.db.add(customer)
                self.db.flush()

            start = datetime.combine(data.date, data.start_time)
            appointment = Appointment(
                business_id=business.id,
                customer_name=data.customer_name,
                customer_phone=data.customer_phone,
                customer_email=data.customer_email,
                customer_id=customer.id,
                service_id=service.id,
                branch_id=data.branch_id if data.branch_id else (staff.branch_id if staff else None),
                staff_id=staff.id if staff else None,
                appointment_date=data.date,
                start_time=data.start_time,
                end_time=(start + timedelta(minutes=duration)).time(),
                status=AppointmentStatus.CONFIRMED if business.online_booking_auto_confirm else AppointmentStatus.PENDING,
                notes=PUBLIC_BOOKING_NOTE,
            )
            self.db.add(appointment)
            self.db.commit()  # releases the advisory lock
        except Exception:
            self.db.rollback()  # also releases the lock
            raise

        self.db.refresh(appointment)
        return BookingResult(appointment=appointment, business=business, service=service, staff=staff, customer=customer)
