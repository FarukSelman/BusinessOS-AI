import uuid
from datetime import datetime, date
from sqlalchemy import String, Text, Boolean, Integer, Numeric, DateTime, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel
from app.shared.enums.package import (
    PackageStatus,
    CustomerPackageStatus,
    SessionStatus,
    InstallmentStatus,
)
from app.shared.enums.invoice import PaymentMethod


class ServicePackage(BaseModel):
    __tablename__ = "service_packages"

    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    services: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    discount_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    validity_days: Mapped[int] = mapped_column(Integer, default=365)
    is_installment_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    max_installments: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[PackageStatus] = mapped_column(SQLEnum(PackageStatus, name="package_status_enum", create_type=False), default=PackageStatus.ACTIVE)


class CustomerPackage(BaseModel):
    __tablename__ = "customer_packages"

    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    package_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("service_packages.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    used_sessions: Mapped[int] = mapped_column(Integer, default=0)
    remaining_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    
    status: Mapped[CustomerPackageStatus] = mapped_column(SQLEnum(CustomerPackageStatus, name="customer_package_status_enum", create_type=False), default=CustomerPackageStatus.ACTIVE)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class PackageSession(BaseModel):
    __tablename__ = "package_sessions"

    customer_package_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customer_packages.id", ondelete="CASCADE"), nullable=False)
    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("services.id", ondelete="SET NULL"), nullable=True)
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    
    session_number: Mapped[int] = mapped_column(Integer, nullable=False)
    session_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    status: Mapped[SessionStatus] = mapped_column(SQLEnum(SessionStatus, name="session_status_enum", create_type=False), default=SessionStatus.PENDING)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class Installment(BaseModel):
    __tablename__ = "installments"

    customer_package_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customer_packages.id", ondelete="CASCADE"), nullable=False)
    business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    status: Mapped[InstallmentStatus] = mapped_column(SQLEnum(InstallmentStatus, name="installment_status_enum", create_type=False), default=InstallmentStatus.PENDING)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(SQLEnum(PaymentMethod, name="payment_method_enum", create_type=False), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
