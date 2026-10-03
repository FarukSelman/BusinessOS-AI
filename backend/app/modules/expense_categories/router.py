from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.modules.expense_categories.schemas import ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryResponse
from app.modules.expense_categories.repository import ExpenseCategoryRepository
from app.modules.expense_categories.service import ExpenseCategoryService
from app.shared.security.business import require_business_member

router = APIRouter(prefix="/businesses/{business_id}/expense-categories", tags=["Expense Categories"], dependencies=[Depends(require_business_member)])

def get_service(db: Session = Depends(get_db)) -> ExpenseCategoryService:
    repository = ExpenseCategoryRepository(db)
    uow = UnitOfWork(db)
    return ExpenseCategoryService(repository=repository, uow=uow)

@router.post("", response_model=ExpenseCategoryResponse, status_code=status.HTTP_201_CREATED)
def create(business_id: UUID, data: ExpenseCategoryCreate, service: ExpenseCategoryService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.create(business_id=business_id, data=data)

@router.get("", response_model=list[ExpenseCategoryResponse])
def list_categories(business_id: UUID, service: ExpenseCategoryService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.list_categories(business_id)

@router.patch("/{id}", response_model=ExpenseCategoryResponse)
def update(business_id: UUID, id: UUID, data: ExpenseCategoryUpdate, service: ExpenseCategoryService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.update(business_id=business_id, category_id=id, data=data)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(business_id: UUID, id: UUID, service: ExpenseCategoryService = Depends(get_service), current_user: User = Depends(get_current_user)):
    service.delete(business_id=business_id, category_id=id)
