import uuid
from sqlalchemy import String, Text, ForeignKey, Float, Integer, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.models.base import BaseModel
from app.shared.enums.loyalty import TransactionType, WalletStatus

class LoyaltyRule(BaseModel):
    __tablename__ = "loyalty_rules"
    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)
    points_per_currency: Mapped[float] = mapped_column(Float, default=1.0)
    min_spend_for_earn: Mapped[float] = mapped_column(Float, default=0.0)
    points_value_in_currency: Mapped[float] = mapped_column(Float, default=0.01)
    min_points_for_spend: Mapped[int] = mapped_column(Integer, default=100)
    expiry_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class LoyaltyWallet(BaseModel):
    __tablename__ = "loyalty_wallets"
    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_earned: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_spent: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[WalletStatus] = mapped_column(String(50), default=WalletStatus.ACTIVE)

    __table_args__ = (
        UniqueConstraint('business_id', 'customer_id', name='uq_loyalty_wallet_business_customer'),
    )

class LoyaltyTransaction(BaseModel):
    __tablename__ = "loyalty_transactions"
    wallet_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("loyalty_wallets.id", ondelete="CASCADE"), nullable=False)
    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(String(50), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
