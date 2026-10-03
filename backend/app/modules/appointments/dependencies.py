from sqlalchemy.orm import Session

from app.db.unit_of_work import UnitOfWork
from app.modules.appointments.repository import AppointmentRepository
from app.modules.appointments.service import AppointmentService
from app.modules.branches.repository import BranchRepository
from app.modules.business_hours.repository import BusinessHoursRepository
from app.modules.business_hours.service import BusinessHoursService
from app.modules.schedule_blocks.repository import ScheduleBlockRepository
from app.modules.staff.repository import StaffProfileRepository, StaffScheduleRepository


def build_appointment_service(db: Session) -> AppointmentService:
    """
    Single place that wires AppointmentService with everything slot
    calculation needs (business hours, staff schedules, schedule blocks).
    Used by the appointments, public booking and agent action routers
    and by the AI appointment tools.
    """
    uow = UnitOfWork(db)
    return AppointmentService(
        repository=AppointmentRepository(db),
        uow=uow,
        schedule_block_repo=ScheduleBlockRepository(db),
        business_hours_service=BusinessHoursService(
            repository=BusinessHoursRepository(db),
            uow=uow,
            branch_repo=BranchRepository(db),
        ),
        staff_schedule_repo=StaffScheduleRepository(db),
        staff_profile_repo=StaffProfileRepository(db),
    )
