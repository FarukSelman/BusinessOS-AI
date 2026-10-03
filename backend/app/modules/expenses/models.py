import uuid
from datetime import date
from sqlalchemy import Enum as SQLEnum, String, Text, Numeric, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.shared.models.base import BaseModel
from app.shared.enums.expense import TransactionDirection, ExpenseStatus, RecurrenceType
from app.shared.enums.invoice import PaymentMethod

class Expense(BaseModel):
    __tablename__ = "expenses"

    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("expense_categories.id"), nullable=True
    )
    direction: Mapped[TransactionDirection] = mapped_column(SQLEnum(TransactionDirection), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TRY")
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ExpenseStatus] = mapped_column(SQLEnum(ExpenseStatus), default=ExpenseStatus.PAID)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(SQLEnum(PaymentMethod), nullable=True)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True
    )
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    recurrence: Mapped[RecurrenceType] = mapped_column(SQLEnum(RecurrenceType), default=RecurrenceType.NONE)
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
