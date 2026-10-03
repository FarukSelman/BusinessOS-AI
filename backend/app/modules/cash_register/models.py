import uuid
from datetime import date, datetime
from sqlalchemy import Enum as SQLEnum, String, Text, Numeric, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.models.base import BaseModel
from app.shared.enums.cash_register import CashRegisterStatus, CashTransactionType

class CashRegister(BaseModel):
    __tablename__ = "cash_registers"

    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True
    )
    opened_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    closed_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    register_date: Mapped[date] = mapped_column(Date, nullable=False)
    opening_balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    closing_balance: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    expected_balance: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    difference: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[CashRegisterStatus] = mapped_column(SQLEnum(CashRegisterStatus), default=CashRegisterStatus.OPEN)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

class CashTransaction(BaseModel):
    __tablename__ = "cash_transactions"

    register_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("cash_registers.id", ondelete="CASCADE"), nullable=False
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False
    )
    transaction_type: Mapped[CashTransactionType] = mapped_column(SQLEnum(CashTransactionType), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
