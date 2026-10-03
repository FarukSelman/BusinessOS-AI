from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.shared.enums.expense import TransactionDirection
from app.modules.expenses.schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse, FinancialSummary
from app.modules.expenses.repository import ExpenseRepository
from app.modules.expenses.service import ExpenseService
from app.shared.security.business import require_business_member

router = APIRouter(prefix="/businesses/{business_id}/expenses", tags=["Expenses"], dependencies=[Depends(require_business_member)])

def get_service(db: Session = Depends(get_db)) -> ExpenseService:
    repository = ExpenseRepository(db)
    uow = UnitOfWork(db)
    return ExpenseService(repository=repository, uow=uow)

@router.post("", response_model=ExpenseResponse, status_code=http_status.HTTP_201_CREATED)
def create(business_id: UUID, data: ExpenseCreate, service: ExpenseService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.create_expense(business_id=business_id, data=data)

# ── Fixed-path routes FIRST ──

@router.get("/summary", response_model=FinancialSummary)
def get_summary(business_id: UUID, start_date: date, end_date: date, service: ExpenseService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.get_summary(business_id, start_date, end_date)

@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    business_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    direction: TransactionDirection | None = None,
    category_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    expense_status: str | None = Query(None, alias="status"),
    service: ExpenseService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_expenses(business_id, page, size, direction, category_id, date_from, date_to, expense_status)

# ── Parameterized routes AFTER ──

@router.patch("/{id}", response_model=ExpenseResponse)
def update(business_id: UUID, id: UUID, data: ExpenseUpdate, service: ExpenseService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.update_expense(business_id=business_id, expense_id=id, data=data)

@router.delete("/{id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete(business_id: UUID, id: UUID, service: ExpenseService = Depends(get_service), current_user: User = Depends(get_current_user)):
    service.delete_expense(business_id=business_id, expense_id=id)
