from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.expense_categories.models import ExpenseCategory

class ExpenseCategoryRepository(BaseRepository[ExpenseCategory]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=ExpenseCategory)

    def list_by_business(self, business_id: UUID) -> list[ExpenseCategory]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.name)
        return list(self.db.scalars(statement).all())

    def get_by_business(self, business_id: UUID, category_id: UUID) -> ExpenseCategory | None:
        statement = select(self.model).where(
            self.model.id == category_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalars(statement).first()
