from uuid import UUID
from datetime import date
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.expenses.models import Expense
from app.shared.enums.expense import TransactionDirection

class ExpenseRepository(BaseRepository[Expense]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Expense)

    def list_by_business(self, business_id: UUID, page: int = 1, size: int = 20, direction: TransactionDirection | None = None, category_id: UUID | None = None, date_from: date | None = None, date_to: date | None = None, status: str | None = None) -> list[Expense]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        if direction:
            query = query.where(self.model.direction == direction)
        if category_id:
            query = query.where(self.model.category_id == category_id)
        if date_from:
            query = query.where(self.model.transaction_date >= date_from)
        if date_to:
            query = query.where(self.model.transaction_date <= date_to)
        if status:
            query = query.where(self.model.status == status)
        
        query = query.order_by(self.model.transaction_date.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())
    
    def get_by_business(self, business_id: UUID, expense_id: UUID) -> Expense | None:
        statement = select(self.model).where(
            self.model.id == expense_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalars(statement).first()

    def get_totals_by_period(self, business_id: UUID, start_date: date, end_date: date) -> dict:
        statement = select(
            self.model.direction, func.sum(self.model.amount)
        ).where(
            self.model.business_id == business_id,
            self.model.transaction_date >= start_date,
            self.model.transaction_date <= end_date,
            self.model.is_deleted.is_(False)
        ).group_by(self.model.direction)
        
        results = self.db.execute(statement).all()
        income = sum([r[1] for r in results if r[0] == TransactionDirection.INCOME]) or 0.0
        expense = sum([r[1] for r in results if r[0] == TransactionDirection.EXPENSE]) or 0.0
        return {"total_income": float(income), "total_expense": float(expense), "net": float(income - expense)}
