from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field
from app.shared.enums.cash_register import CashRegisterStatus, CashTransactionType

class CashRegisterOpen(BaseModel):
    opening_balance: float = 0
    branch_id: UUID | None = None
    notes: str | None = None

class CashRegisterClose(BaseModel):
    closing_balance: float
    notes: str | None = None

class CashRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    branch_id: UUID | None
    register_date: date
    opening_balance: float
    closing_balance: float | None
    expected_balance: float | None
    difference: float | None
    status: CashRegisterStatus
    opened_at: datetime
    closed_at: datetime | None
    notes: str | None
    created_at: datetime

class CashTransactionCreate(BaseModel):
    transaction_type: CashTransactionType
    amount: float = Field(..., gt=0)
    description: str | None = Field(None, max_length=500)
    reference_type: str | None = Field(None, max_length=50)
    reference_id: UUID | None = None

class CashTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    register_id: UUID
    transaction_type: CashTransactionType
    amount: float
    description: str | None
    reference_type: str | None
    reference_id: UUID | None
    created_at: datetime

class RegisterSummary(BaseModel):
    opening_balance: float
    total_sales: float
    total_expenses: float
    total_deposits: float
    total_withdrawals: float
    expected_closing: float
    actual_closing: float | None = None
    difference: float | None = None
