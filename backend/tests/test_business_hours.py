"""
Slot calculation with business hours, branch overrides, staff schedules
and schedule blocks. Uses in-memory fake repositories, no database needed.
"""
from datetime import date, time
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.appointments.service import AppointmentService
from app.modules.business_hours.schemas import BusinessHoursItem, BusinessHoursSet
from app.modules.business_hours.service import BusinessHoursService
from app.shared.enums.appointment import AppointmentStatus
from app.shared.enums.schedule_block import BlockType

BUSINESS = uuid4()
BRANCH = uuid4()
STAFF = uuid4()
MONDAY = date(2026, 10, 5)  # weekday() == 0


# ---------------------------------------------------------------- fakes

class FakeHoursRepo:
    def __init__(self, rows=None):
        self.rows = rows or []

    def list_for_scope(self, business_id, branch_id=None):
        return sorted(
            [r for r in self.rows if r.business_id == business_id and r.branch_id == branch_id],
            key=lambda r: r.day_of_week,
        )


def hours(day, open_t=None, close_t=None, closed=False, branch_id=None):
    return SimpleNamespace(
        business_id=BUSINESS, branch_id=branch_id, day_of_week=day,
        open_time=open_t, close_time=close_t, is_closed=closed,
    )


class FakeAppointmentRepo:
    def __init__(self, appointments=None):
        self.appointments = appointments or []

    def list_by_date(self, business_id, target_date):
        return self.appointments

    def list_by_staff(self, business_id, staff_id, target_date):
        return [a for a in self.appointments if a.staff_id == staff_id]

    def list_by_branch(self, business_id, branch_id, target_date):
        return [a for a in self.appointments if a.branch_id == branch_id]


def appt(start, end, staff_id=None, branch_id=None, status=AppointmentStatus.CONFIRMED):
    return SimpleNamespace(start_time=start, end_time=end, staff_id=staff_id, branch_id=branch_id, status=status)


class FakeBlockRepo:
    def __init__(self, blocks=None):
        self.blocks = blocks or []
        self.last_branch_id = "not-called"

    def list_active_blocks_for_date(self, business_id, target_date, branch_id=None):
        self.last_branch_id = branch_id
        return [b for b in self.blocks if b.branch_id is None or b.branch_id == branch_id]


def block(block_type, start=None, end=None, branch_id=None):
    return SimpleNamespace(block_type=block_type, start_time=start, end_time=end, branch_id=branch_id)


class FakeStaffScheduleRepo:
    def __init__(self, rows=None):
        self.rows = rows or []

    def get_schedule_for_staff(self, staff_id):
        return [r for r in self.rows if r.staff_id == staff_id]


def shift(day, start, end, working=True):
    return SimpleNamespace(staff_id=STAFF, day_of_week=day, start_time=start, end_time=end, is_working=working)


class FakeStaffProfileRepo:
    def __init__(self, branch_id=None):
        self.branch_id = branch_id

    def get_by_business(self, business_id, staff_id):
        return SimpleNamespace(id=staff_id, branch_id=self.branch_id)


def make_service(hours_rows=None, appointments=None, blocks=None, shifts=None, staff_branch=None):
    block_repo = FakeBlockRepo(blocks)
    service = AppointmentService(
        repository=FakeAppointmentRepo(appointments),
        uow=None,
        schedule_block_repo=block_repo,
        business_hours_service=BusinessHoursService(repository=FakeHoursRepo(hours_rows), uow=None),
        staff_schedule_repo=FakeStaffScheduleRepo(shifts),
        staff_profile_repo=FakeStaffProfileRepo(staff_branch),
    )
    return service, block_repo


# ---------------------------------------------------------------- business hours

def test_no_hours_configured_falls_back_to_9_to_18():
    service, _ = make_service()
    slots = service.get_available_slots(BUSINESS, MONDAY, duration_minutes=60)
    assert slots[0] == "09:00"
    assert slots[-1] == "17:00"


def test_business_hours_define_the_window():
    service, _ = make_service([hours(0, time(10), time(14))])
    slots = service.get_available_slots(BUSINESS, MONDAY, duration_minutes=60)
    assert slots == ["10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00"]


def test_closed_day_returns_no_slots():
    service, _ = make_service([hours(0, closed=True), hours(1, time(9), time(17))])
    assert service.get_available_slots(BUSINESS, MONDAY) == []


def test_missing_day_in_configured_week_counts_as_closed():
    service, _ = make_service([hours(1, time(9), time(17))])  # only Tuesday configured
    assert service.get_available_slots(BUSINESS, MONDAY) == []


def test_branch_week_overrides_business_week():
    service, _ = make_service([
        hours(0, time(9), time(18)),
        hours(0, time(13), time(15), branch_id=BRANCH),
    ])
    slots = service.get_available_slots(BUSINESS, MONDAY, duration_minutes=60, branch_id=BRANCH)
    assert slots == ["13:00", "13:30", "14:00"]


def test_branch_without_own_week_uses_business_week():
    service, _ = make_service([hours(0, time(10), time(12))])
    slots = service.get_available_slots(BUSINESS, MONDAY, duration_minutes=60, branch_id=BRANCH)
    assert slots == ["10:00", "10:30", "11:00"]


# ---------------------------------------------------------------- staff

def test_staff_hours_are_intersected_with_business_hours():
    service, _ = make_service([hours(0, time(9), time(18))], shifts=[shift(0, time(12), time(20))])
    slots = service.get_available_slots(BUSINESS, MONDAY, duration_minutes=60, staff_id=STAFF)
    assert slots[0] == "12:00"
    assert slots[-1] == "17:00"


def test_staff_not_working_that_day_returns_no_slots():
    service, _ = make_service(shifts=[shift(0, time(9), time(18), working=False)])
    assert service.get_available_slots(BUSINESS, MONDAY, staff_id=STAFF) == []


def test_staff_with_schedule_but_no_row_for_the_day_returns_no_slots():
    service, _ = make_service(shifts=[shift(2, time(9), time(18))])  # works Wednesdays only
    assert service.get_available_slots(BUSINESS, MONDAY, staff_id=STAFF) == []


def test_staff_without_any_schedule_is_not_restricted():
    service, _ = make_service([hours(0, time(10), time(12))])
    slots = service.get_available_slots(BUSINESS, MONDAY, duration_minutes=60, staff_id=STAFF)
    assert slots == ["10:00", "10:30", "11:00"]


def test_staff_and_business_hours_without_overlap_returns_no_slots():
    service, _ = make_service([hours(0, time(9), time(12))], shifts=[shift(0, time(13), time(18))])
    assert service.get_available_slots(BUSINESS, MONDAY, staff_id=STAFF) == []


def test_staff_branch_is_used_when_no_branch_given():
    service, block_repo = make_service(
        [hours(0, time(9), time(18)), hours(0, time(15), time(17), branch_id=BRANCH)],
        staff_branch=BRANCH,
    )
    slots = service.get_available_slots(BUSINESS, MONDAY, duration_minutes=60, staff_id=STAFF)
    assert slots == ["15:00", "15:30", "16:00"]
    assert block_repo.last_branch_id == BRANCH


# ---------------------------------------------------------------- blocks and appointments

def test_time_range_block_removes_overlapping_slots():
    service, _ = make_service(
        [hours(0, time(9), time(12))],
        blocks=[block(BlockType.TIME_RANGE, time(10), time(11))],
    )
    slots = service.get_available_slots(BUSINESS, MONDAY, duration_minutes=60)
    assert slots == ["09:00", "11:00"]


def test_full_day_block_closes_the_day():
    service, _ = make_service(blocks=[block(BlockType.FULL_DAY)])
    assert service.get_available_slots(BUSINESS, MONDAY) == []


def test_branch_block_does_not_affect_other_scope():
    service, _ = make_service(blocks=[block(BlockType.FULL_DAY, branch_id=BRANCH)])
    assert service.get_available_slots(BUSINESS, MONDAY) != []
    assert service.get_available_slots(BUSINESS, MONDAY, branch_id=BRANCH) == []


def test_existing_appointment_removes_slots_but_cancelled_does_not():
    service, _ = make_service(
        [hours(0, time(9), time(11))],
        appointments=[
            appt(time(9), time(10)),
            appt(time(10), time(11), status=AppointmentStatus.CANCELLED),
        ],
    )
    slots = service.get_available_slots(BUSINESS, MONDAY, duration_minutes=60)
    assert slots == ["10:00"]


# ---------------------------------------------------------------- schemas

def test_schema_rejects_open_after_close():
    with pytest.raises(ValidationError):
        BusinessHoursItem(day_of_week=0, open_time=time(18), close_time=time(9))


def test_schema_requires_times_on_open_day():
    with pytest.raises(ValidationError):
        BusinessHoursItem(day_of_week=0, open_time=time(9))


def test_schema_clears_times_on_closed_day():
    item = BusinessHoursItem(day_of_week=6, open_time=time(9), close_time=time(18), is_closed=True)
    assert item.open_time is None and item.close_time is None


def test_schema_rejects_duplicate_days():
    with pytest.raises(ValidationError):
        BusinessHoursSet(items=[
            BusinessHoursItem(day_of_week=0, open_time=time(9), close_time=time(18)),
            BusinessHoursItem(day_of_week=0, is_closed=True),
        ])
