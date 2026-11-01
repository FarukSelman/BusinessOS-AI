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
    InstallmentResponse, OverdueInstallmentResponse, PackageSessionResponse,
    customer_package_view, installment_view,
)
from app.shared.enums.package import PackageStatus, CustomerPackageStatus, InstallmentStatus
from app.shared.enums.invoice import PaymentMethod
from app.ai.agents.tools.common import can_view_finance
from app.modules.membership.models import Membership
from app.shared.security.business import (
    get_business_membership,
    require_business_member,
    require_finance,
    require_staff,
)

# Reading: every member; customer payments and installment amounts are None for
# roles without finance access (package prices are sale prices and stay).
# Writing: package catalogue and collecting installments for owner/admin;
# selling a package and marking sessions for everyone but viewers.


packages_router = APIRouter(prefix="/businesses/{business_id}/packages", tags=["Packages"], dependencies=[Depends(require_business_member)])
customer_packages_router = APIRouter(prefix="/businesses/{business_id}/customer-packages", tags=["Customer Packages"], dependencies=[Depends(require_business_member)])
installments_router = APIRouter(prefix="/businesses/{business_id}/installments", tags=["Installments"], dependencies=[Depends(require_business_member)])


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
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
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
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    return service.update_package(business_id, package_id, data)

@packages_router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    business_id: UUID,
    package_id: UUID,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
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
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(require_staff),
):
    cp = service.sell_package(business_id, data)
    detail = service.get_customer_package_detail(business_id, cp.id)
    return customer_package_view(detail, can_view_finance(membership.role))

@customer_packages_router.get("", response_model=list[CustomerPackageResponse])
def list_customer_packages(
    business_id: UUID,
    customer_id: Optional[UUID] = Query(None),
    status: Optional[CustomerPackageStatus] = Query(None),
    pagination: PaginationParams = Depends(),
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    cps = service.list_customer_packages(business_id, pagination.page, pagination.size, status, customer_id)
    show = can_view_finance(membership.role)
    return [customer_package_view(cp, show) for cp in cps]

@customer_packages_router.get("/{cp_id}", response_model=CustomerPackageResponse)
def get_customer_package_detail(
    business_id: UUID,
    cp_id: UUID,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    return customer_package_view(service.get_customer_package_detail(business_id, cp_id), can_view_finance(membership.role))

@customer_packages_router.post("/{cp_id}/sessions/{session_id}/complete", response_model=PackageSessionResponse)
def complete_session(
    business_id: UUID,
    cp_id: UUID,
    session_id: UUID,
    data: SessionComplete,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user),
    _staff: Membership = Depends(require_staff),
):
    return service.complete_session(business_id, cp_id, session_id, data)

@customer_packages_router.post("/{cp_id}/sessions/{session_id}/cancel", response_model=PackageSessionResponse)
def cancel_session(
    business_id: UUID,
    cp_id: UUID,
    session_id: UUID,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user),
    _staff: Membership = Depends(require_staff),
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
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    show = can_view_finance(membership.role)
    return [installment_view(i, show) for i in service.list_installments(business_id, pagination.page, pagination.size, status)]

@installments_router.get("/overdue", response_model=list[InstallmentResponse])
def list_overdue_installments(
    business_id: UUID,
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    show = can_view_finance(membership.role)
    return [installment_view(i, show) for i in service.list_overdue_installments(business_id)]

@installments_router.post("/{installment_id}/pay", response_model=InstallmentResponse)
def pay_installment(
    business_id: UUID,
    installment_id: UUID,
    payment_method: Optional[PaymentMethod] = Query(None),
    service: PackageService = Depends(get_package_service),
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    return installment_view(service.pay_installment(business_id, installment_id, payment_method), True)
