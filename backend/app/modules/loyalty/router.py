from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.modules.loyalty.schemas import LoyaltyRuleUpdate, LoyaltyRuleResponse, LoyaltyWalletResponse, LoyaltyTransactionResponse, EarnPointsRequest, SpendPointsRequest, AdjustPointsRequest
from app.modules.loyalty.repository import LoyaltyRuleRepository, LoyaltyWalletRepository, LoyaltyTransactionRepository
from app.modules.loyalty.service import LoyaltyService
from app.shared.security.business import require_business_member

router = APIRouter(prefix="/businesses/{business_id}/loyalty", tags=["Loyalty"], dependencies=[Depends(require_business_member)])

def get_service(db: Session = Depends(get_db)) -> LoyaltyService:
    rule_repo = LoyaltyRuleRepository(db)
    wallet_repo = LoyaltyWalletRepository(db)
    transaction_repo = LoyaltyTransactionRepository(db)
    uow = UnitOfWork(db)
    return LoyaltyService(rule_repo, wallet_repo, transaction_repo, uow)

@router.get("/rules", response_model=LoyaltyRuleResponse)
def get_rules(
    business_id: UUID,
    service: LoyaltyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_or_create_rule(business_id)

@router.put("/rules", response_model=LoyaltyRuleResponse)
def update_rules(
    business_id: UUID,
    data: LoyaltyRuleUpdate,
    service: LoyaltyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.update_rule(business_id, data)

@router.get("/wallets", response_model=List[LoyaltyWalletResponse])
def list_wallets(
    business_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: LoyaltyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_wallets(business_id, page, size)

@router.get("/wallets/{customer_id}", response_model=LoyaltyWalletResponse)
def get_customer_wallet(
    business_id: UUID,
    customer_id: UUID,
    service: LoyaltyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_wallet_balance(business_id, customer_id)

@router.post("/earn", response_model=LoyaltyTransactionResponse)
def earn_points(
    business_id: UUID,
    data: EarnPointsRequest,
    service: LoyaltyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.earn_points(
        business_id=business_id,
        customer_id=data.customer_id,
        points=data.points,
        description=data.description,
        reference_type=data.reference_type,
        reference_id=data.reference_id
    )

@router.post("/spend", response_model=LoyaltyTransactionResponse)
def spend_points(
    business_id: UUID,
    data: SpendPointsRequest,
    service: LoyaltyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.spend_points(
        business_id=business_id,
        customer_id=data.customer_id,
        points=data.points,
        description=data.description,
        reference_type=data.reference_type,
        reference_id=data.reference_id
    )

@router.post("/adjust", response_model=LoyaltyTransactionResponse)
def adjust_points(
    business_id: UUID,
    data: AdjustPointsRequest,
    service: LoyaltyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.adjust_points(
        business_id=business_id,
        customer_id=data.customer_id,
        points=data.points,
        description=data.description
    )

@router.get("/transactions", response_model=List[LoyaltyTransactionResponse])
def list_transactions(
    business_id: UUID,
    customer_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: LoyaltyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_transactions(business_id, customer_id, page, size)
