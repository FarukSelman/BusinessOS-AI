from uuid import UUID
from datetime import date
from app.db.unit_of_work import UnitOfWork
from app.modules.expenses.repository import ExpenseRepository
from app.modules.expenses.models import Expense
from app.modules.expenses.schemas import ExpenseCreate, ExpenseUpdate, FinancialSummary
from app.core.exceptions import NotFoundException
from app.shared.enums.expense import TransactionDirection, ExpenseStatus

class ExpenseService:
    def __init__(self, repository: ExpenseRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    def create_expense(self, business_id: UUID, data: ExpenseCreate) -> Expense:
        obj = Expense(
            business_id=business_id,
            branch_id=data.branch_id,
            category_id=data.category_id,
            direction=data.direction,
            title=data.title,
            description=data.description,
            amount=data.amount,
            currency=data.currency,
            transaction_date=data.transaction_date,
            status=ExpenseStatus.PAID,
            payment_method=data.payment_method,
            receipt_url=data.receipt_url,
            recurrence=data.recurrence,
            tags=data.tags
        )
        with self.uow:
            self.repository.create(obj)
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def list_expenses(self, business_id: UUID, page: int = 1, size: int = 20, direction: TransactionDirection | None = None, category_id: UUID | None = None, date_from: date | None = None, date_to: date | None = None, status: str | None = None) -> list[Expense]:
        return self.repository.list_by_business(business_id, page, size, direction, category_id, date_from, date_to, status)

    def update_expense(self, business_id: UUID, expense_id: UUID, data: ExpenseUpdate) -> Expense:
        obj = self.repository.get_by_business(business_id, expense_id)
        if not obj:
            raise NotFoundException("Expense not found")
        with self.uow:
            for k, v in data.model_dump(exclude_unset=True).items():
                setattr(obj, k, v)
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def delete_expense(self, business_id: UUID, expense_id: UUID) -> None:
        obj = self.repository.get_by_business(business_id, expense_id)
        if not obj:
            raise NotFoundException("Expense not found")
        with self.uow:
            self.repository.soft_delete(obj)
            self.uow.flush()

    def get_summary(self, business_id: UUID, start_date: date, end_date: date) -> FinancialSummary:
        totals = self.repository.get_totals_by_period(business_id, start_date, end_date)
        return FinancialSummary(
            total_income=totals["total_income"],
            total_expense=totals["total_expense"],
            net_profit=totals["net"],
            period_start=start_date,
            period_end=end_date
        )

    def create_income_from_invoice(self, business_id: UUID, invoice: dict) -> None:
        # Dummy method to show it exists, full implementation uses Invoice object
        pass
