from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.shared.enums.loyalty import TransactionType, WalletStatus

class LoyaltyRuleCreate(BaseModel):
    points_per_currency: float = 1.0
    min_spend_for_earn: float = 0.0
    points_value_in_currency: float = 0.01
    min_points_for_spend: int = 100
    expiry_days: Optional[int] = None
    is_active: bool = True

class LoyaltyRuleUpdate(LoyaltyRuleCreate):
    pass

class LoyaltyRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    points_per_currency: float
    min_spend_for_earn: float
    points_value_in_currency: float
    min_points_for_spend: int
    expiry_days: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class LoyaltyWalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    customer_id: UUID
    balance: int
    lifetime_earned: int
    lifetime_spent: int
    status: WalletStatus
    created_at: datetime
    updated_at: datetime

class LoyaltyTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    wallet_id: UUID
    business_id: UUID
    transaction_type: TransactionType
    points: int
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

class EarnPointsRequest(BaseModel):
    customer_id: UUID
    points: int
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None

class SpendPointsRequest(BaseModel):
    customer_id: UUID
    points: int
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None

class AdjustPointsRequest(BaseModel):
    customer_id: UUID
    points: int
    description: Optional[str] = None
