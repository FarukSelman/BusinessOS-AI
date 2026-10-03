from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.core.pagination import PaginationParams

from app.modules.packages.repository import ServicePackageRepository, CustomerPackageRepository, PackageSessionRepository, InstallmentRepository
from app.modules.packages.service import PackageService
from app.modules.packages.schemas import (
    PackageCreate, PackageUpdate, PackageResponse,
    PackageSaleCreate, CustomerPackageResponse, SessionComplete,
    InstallmentResponse, OverdueInstallmentResponse, PackageSessionResponse
)
from app.shared.enums.package import PackageStatus, CustomerPackageStatus, InstallmentStatus
from app.shared.enums.invoice import PaymentMethod


packages_router = APIRouter(prefix="/businesses/{business_id}/packages", tags=["Packages"])
customer_packages_router = APIRouter(prefix="/businesses/{business_id}/customer-packages", tags=["Customer Packages"])
installments_router = APIRouter(prefix="/businesses/{business_id}/installments", tags=["Installments"])


def get_package_service(db: Session = Depends(get_db)) -> PackageService:
    package_repo = ServicePackageRepository(db)
    cp_repo = CustomerPackageRepository(db)
    session_repo = PackageSessionRepository(db)
    installment_repo = InstallmentRepository(db)
    uow = UnitOfWork(db)
    return PackageService(
        package_repo=package_repo,
        customer_package_repo=cp_repo,
        session_repo=session_repo,
        installment_repo=installment_repo,
        uow=uow
    )

# ==========================================
# Packages Router
# ==========================================

@packages_router.post("", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
def create_package(
    business_id: UUID, 
    data: PackageCreate, 
    service: PackageService = Depends(get_package_service), 
    current_user: User = Depends(get_current_user)
):
    return service.create_package(business_id, data)

@packages_router.get("", response_model=list[PackageResponse])
def list_packages(
    business_id: UUID,
    status: Optional[PackageStatus] = Query(None),
    pagination: PaginationParams = Depends(),
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_packages(business_id, pagination.page, pagination.size, status)

@packages_router.get("/{package_id}", response_model=PackageResponse)
def get_package(
    business_id: UUID,
    package_id: UUID,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_package(business_id, package_id)

@packages_router.patch("/{package_id}", response_model=PackageResponse)
def update_package(
    business_id: UUID,
    package_id: UUID,
    data: PackageUpdate,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    return service.update_package(business_id, package_id, data)

@packages_router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    business_id: UUID,
    package_id: UUID,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    service.delete_package(business_id, package_id)

# ==========================================
# Customer Packages Router
# ==========================================

@customer_packages_router.post("", response_model=CustomerPackageResponse, status_code=status.HTTP_201_CREATED)
def sell_package(
    business_id: UUID,
    data: PackageSaleCreate,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    cp = service.sell_package(business_id, data)
    return service.get_customer_package_detail(business_id, cp.id)

@customer_packages_router.get("", response_model=list[CustomerPackageResponse])
def list_customer_packages(
    business_id: UUID,
    customer_id: Optional[UUID] = Query(None),
    status: Optional[CustomerPackageStatus] = Query(None),
    pagination: PaginationParams = Depends(),
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    cps = service.list_customer_packages(business_id, pagination.page, pagination.size, status, customer_id)
    # the list does not include full nested relations, which is fine based on common patterns
    return cps

@customer_packages_router.get("/{cp_id}", response_model=CustomerPackageResponse)
def get_customer_package_detail(
    business_id: UUID,
    cp_id: UUID,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_customer_package_detail(business_id, cp_id)

@customer_packages_router.post("/{cp_id}/sessions/{session_id}/complete", response_model=PackageSessionResponse)
def complete_session(
    business_id: UUID,
    cp_id: UUID,
    session_id: UUID,
    data: SessionComplete,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    return service.complete_session(business_id, cp_id, session_id, data)

@customer_packages_router.post("/{cp_id}/sessions/{session_id}/cancel", response_model=PackageSessionResponse)
def cancel_session(
    business_id: UUID,
    cp_id: UUID,
    session_id: UUID,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    return service.cancel_session(business_id, cp_id, session_id)


# ==========================================
# Installments Router
# ==========================================

@installments_router.get("", response_model=list[InstallmentResponse])
def list_installments(
    business_id: UUID,
    status: Optional[InstallmentStatus] = Query(None),
    pagination: PaginationParams = Depends(),
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_installments(business_id, pagination.page, pagination.size, status)

@installments_router.get("/overdue", response_model=list[InstallmentResponse])
def list_overdue_installments(
    business_id: UUID,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_overdue_installments(business_id)

@installments_router.post("/{installment_id}/pay", response_model=InstallmentResponse)
def pay_installment(
    business_id: UUID,
    installment_id: UUID,
    payment_method: Optional[PaymentMethod] = Query(None),
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user)
):
    return service.pay_installment(business_id, installment_id, payment_method)
