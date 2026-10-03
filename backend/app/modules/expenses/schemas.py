from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field
from app.shared.enums.expense import TransactionDirection, ExpenseStatus, RecurrenceType
from app.shared.enums.invoice import PaymentMethod

class ExpenseCreate(BaseModel):
    direction: TransactionDirection
    title: str = Field(..., max_length=200)
    description: str | None = None
    amount: float = Field(..., gt=0)
    currency: str = Field("TRY", max_length=3)
    transaction_date: date
    category_id: UUID | None = None
    branch_id: UUID | None = None
    payment_method: PaymentMethod | None = None
    receipt_url: str | None = Field(None, max_length=500)
    recurrence: RecurrenceType = RecurrenceType.NONE
    tags: str | None = Field(None, max_length=500)

class ExpenseUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    amount: float | None = Field(None, gt=0)
    transaction_date: date | None = None
    category_id: UUID | None = None
    status: ExpenseStatus | None = None
    payment_method: PaymentMethod | None = None
    receipt_url: str | None = Field(None, max_length=500)
    recurrence: RecurrenceType | None = None
    tags: str | None = Field(None, max_length=500)

class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    branch_id: UUID | None
    category_id: UUID | None
    direction: TransactionDirection
    title: str
    description: str | None
    amount: float
    currency: str
    transaction_date: date
    status: ExpenseStatus
    payment_method: PaymentMethod | None
    invoice_id: UUID | None
    receipt_url: str | None
    recurrence: RecurrenceType
    is_auto_generated: bool
    tags: str | None
    created_at: datetime
    updated_at: datetime

class FinancialSummary(BaseModel):
    total_income: float
    total_expense: float
    net_profit: float
    period_start: date
    period_end: date

class CategoryBreakdown(BaseModel):
    category_name: str
    category_color: str
    total_amount: float
    percentage: float

class MonthlyReport(BaseModel):
    year: int
    month: int
    income: float
    expense: float
    net: float
    category_breakdown: list[CategoryBreakdown]
    daily_totals: list[dict]


class ExpenseCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    name: str
    color: str | None
    icon: str | None
    is_default: bool


class ExpenseCategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    color: str | None = Field(None, max_length=20)
    icon: str | None = Field(None, max_length=50)
