import uuid
from datetime import date, time
from typing import List, Optional, Tuple

from app.core.exceptions import NotFoundException
from app.db.unit_of_work import UnitOfWork
from app.modules.branches.repository import BranchRepository
from app.modules.business_hours.models import BusinessHours
from app.modules.business_hours.repository import BusinessHoursRepository
from app.modules.business_hours.schemas import BusinessHoursSet

# Used when a business has not configured any hours yet, so existing
# businesses keep the previous behaviour (09:00-18:00 every day).
DEFAULT_OPEN_TIME = time(9, 0)
DEFAULT_CLOSE_TIME = time(18, 0)


class BusinessHoursService:
    def __init__(
        self,
        repository: BusinessHoursRepository,
        uow: UnitOfWork,
        branch_repo: Optional[BranchRepository] = None,
    ):
        self.repository = repository
        self.uow = uow
        self.branch_repo = branch_repo

    def _ensure_branch(self, business_id: uuid.UUID, branch_id: Optional[uuid.UUID]) -> None:
        if branch_id is None or self.branch_repo is None:
            return
        if self.branch_repo.get_by_business(business_id, branch_id) is None:
            raise NotFoundException("Branch not found")

    def get_hours(self, business_id: uuid.UUID, branch_id: Optional[uuid.UUID] = None) -> List[BusinessHours]:
        self._ensure_branch(business_id, branch_id)
        return self.repository.list_for_scope(business_id, branch_id)

    def set_hours(
        self,
        business_id: uuid.UUID,
        data: BusinessHoursSet,
        branch_id: Optional[uuid.UUID] = None,
    ) -> List[BusinessHours]:
        self._ensure_branch(business_id, branch_id)

        with self.uow:
            self.repository.remove_all_for_scope(business_id, branch_id)

            rows = []
            for item in data.items:
                row = BusinessHours(
                    business_id=business_id,
                    branch_id=branch_id,
                    day_of_week=item.day_of_week,
                    open_time=item.open_time,
                    close_time=item.close_time,
                    is_closed=item.is_closed,
                )
                self.repository.create(row)
                rows.append(row)

            self.uow.flush()

        return sorted(rows, key=lambda r: r.day_of_week)

    def reset_branch_hours(self, business_id: uuid.UUID, branch_id: uuid.UUID) -> None:
        """Delete a branch's own week so it falls back to the business-wide hours."""
        self._ensure_branch(business_id, branch_id)
        with self.uow:
            self.repository.remove_all_for_scope(business_id, branch_id)

    def get_open_window(
        self,
        business_id: uuid.UUID,
        target_date: date,
        branch_id: Optional[uuid.UUID] = None,
    ) -> Optional[Tuple[time, time]]:
        """
        Opening window for a date, or None if closed.

        Resolution order:
          1. the branch's own week (if the branch has any rows)
          2. the business-wide week (if it has any rows)
          3. DEFAULT_OPEN_TIME - DEFAULT_CLOSE_TIME (nothing configured yet)
        Inside a configured week, a missing day counts as closed.
        """
        rows: List[BusinessHours] = []
        if branch_id is not None:
            rows = self.repository.list_for_scope(business_id, branch_id)
        if not rows:
            rows = self.repository.list_for_scope(business_id, None)
        if not rows:
            return DEFAULT_OPEN_TIME, DEFAULT_CLOSE_TIME

        weekday = target_date.weekday()
        day = next((r for r in rows if r.day_of_week == weekday), None)
        if day is None or day.is_closed or day.open_time is None or day.close_time is None:
            return None
        return day.open_time, day.close_time
