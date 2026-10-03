from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID

from app.shared.enums.package import PackageStatus, CustomerPackageStatus, SessionStatus, InstallmentStatus
from app.shared.enums.invoice import PaymentMethod


class PackageServiceItem(BaseModel):
    service_id: UUID
    service_name: str
    session_count: int


class PackageCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    services: List[PackageServiceItem]
    price: float
    discount_percentage: float = 0.0
    validity_days: int = 365
    is_installment_allowed: bool = True
    max_installments: int = 1


class PackageUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    services: Optional[List[PackageServiceItem]] = None
    price: Optional[float] = None
    discount_percentage: Optional[float] = None
    validity_days: Optional[int] = None
    is_installment_allowed: Optional[bool] = None
    max_installments: Optional[int] = None
    status: Optional[PackageStatus] = None


class PackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    name: str
    description: Optional[str]
    services: List[dict]
    total_sessions: int
    price: float
    discount_percentage: float
    validity_days: int
    is_installment_allowed: bool
    max_installments: int
    status: PackageStatus
    created_at: datetime
    updated_at: datetime


class PackageSaleCreate(BaseModel):
    customer_id: UUID
    package_id: UUID
    branch_id: Optional[UUID] = None
    installment_count: int = 1
    payment_method: Optional[PaymentMethod] = None
    notes: Optional[str] = None


class SessionComplete(BaseModel):
    appointment_id: Optional[UUID] = None
    staff_id: Optional[UUID] = None
    notes: Optional[str] = None


class InstallmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    customer_package_id: UUID
    business_id: UUID
    customer_id: UUID
    installment_number: int
    amount: float
    due_date: date
    paid_date: Optional[date]
    status: InstallmentStatus
    payment_method: Optional[PaymentMethod]
    notes: Optional[str]


class PackageSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    customer_package_id: UUID
    business_id: UUID
    service_id: Optional[UUID]
    appointment_id: Optional[UUID]
    session_number: int
    session_date: Optional[datetime]
    status: SessionStatus
    notes: Optional[str]
    completed_by: Optional[UUID]


class CustomerPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    customer_id: UUID
    package_id: UUID
    branch_id: Optional[UUID]
    purchased_at: datetime
    expires_at: Optional[datetime]
    total_sessions: int
    used_sessions: int
    remaining_sessions: int
    total_price: float
    paid_amount: float
    status: CustomerPackageStatus
    notes: Optional[str]
    sessions: List[PackageSessionResponse] = []
    installments: List[InstallmentResponse] = []


class OverdueInstallmentResponse(InstallmentResponse):
    customer_name: Optional[str] = None
    package_name: Optional[str] = None
