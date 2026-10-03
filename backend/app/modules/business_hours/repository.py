import uuid
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository
from app.modules.business_hours.models import BusinessHours


class BusinessHoursRepository(BaseRepository[BusinessHours]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=BusinessHours)

    def _scope(self, statement, business_id: uuid.UUID, branch_id: uuid.UUID | None):
        statement = statement.where(self.model.business_id == business_id)
        if branch_id is None:
            return statement.where(self.model.branch_id.is_(None))
        return statement.where(self.model.branch_id == branch_id)

    def list_for_scope(self, business_id: uuid.UUID, branch_id: uuid.UUID | None = None) -> List[BusinessHours]:
        statement = self._scope(select(self.model), business_id, branch_id).where(
            self.model.is_deleted.is_(False),
        ).order_by(self.model.day_of_week)
        return list(self.db.scalars(statement).all())

    def remove_all_for_scope(self, business_id: uuid.UUID, branch_id: uuid.UUID | None = None) -> None:
        # Hard delete, same as StaffScheduleRepository: the week is always replaced as a whole.
        self.db.execute(self._scope(delete(self.model), business_id, branch_id))
