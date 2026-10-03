from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.modules.cash_register.schemas import CashRegisterOpen, CashRegisterClose, CashRegisterResponse, CashTransactionCreate, CashTransactionResponse, RegisterSummary
from app.modules.cash_register.repository import CashRegisterRepository, CashTransactionRepository
from app.modules.cash_register.service import CashRegisterService
from app.shared.security.business import require_business_member

router = APIRouter(prefix="/businesses/{business_id}/cash-register", tags=["Cash Register"], dependencies=[Depends(require_business_member)])

def get_service(db: Session = Depends(get_db)) -> CashRegisterService:
    register_repo = CashRegisterRepository(db)
    transaction_repo = CashTransactionRepository(db)
    uow = UnitOfWork(db)
    return CashRegisterService(register_repo=register_repo, transaction_repo=transaction_repo, uow=uow)

# ── Fixed-path routes FIRST (before /{register_id} catch-all) ──

@router.post("/open", response_model=CashRegisterResponse, status_code=status.HTTP_201_CREATED)
def open_register(business_id: UUID, data: CashRegisterOpen, service: CashRegisterService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.open_register(business_id=business_id, data=data, user_id=current_user.id)

@router.get("/today", response_model=CashRegisterResponse)
def get_today_register(business_id: UUID, service: CashRegisterService = Depends(get_service), current_user: User = Depends(get_current_user)):
    """Bugünkü kasayı döndürür. Yoksa 404."""
    today = date.today()
    register = service.register_repo.get_by_date(business_id, today)
    if not register:
        raise HTTPException(status_code=404, detail="Bugün için açılmış kasa bulunamadı.")
    return register

@router.get("", response_model=list[CashRegisterResponse])
def list_registers(business_id: UUID, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), service: CashRegisterService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.register_repo.list_by_business(business_id, page, size)

# ── Parameterized routes AFTER fixed paths ──

@router.post("/{register_id}/close", response_model=CashRegisterResponse)
def close_register(business_id: UUID, register_id: UUID, data: CashRegisterClose, service: CashRegisterService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.close_register(business_id=business_id, register_id=register_id, data=data, user_id=current_user.id)

@router.post("/{register_id}/transactions", response_model=CashTransactionResponse, status_code=status.HTTP_201_CREATED)
def add_transaction(business_id: UUID, register_id: UUID, data: CashTransactionCreate, service: CashRegisterService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.add_transaction(business_id=business_id, register_id=register_id, data=data, user_id=current_user.id)

@router.get("/{register_id}/summary", response_model=RegisterSummary)
def get_summary(business_id: UUID, register_id: UUID, service: CashRegisterService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.get_register_summary(register_id, business_id=business_id)

@router.get("/{register_id}", response_model=CashRegisterResponse)
def get_register(business_id: UUID, register_id: UUID, service: CashRegisterService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.get_register(business_id, register_id)
