from typing import List, Optional
from uuid import UUID
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from app.core.exceptions import NotFoundException, BadRequestException
from app.db.unit_of_work import UnitOfWork
from app.modules.packages.repository import ServicePackageRepository, CustomerPackageRepository, PackageSessionRepository, InstallmentRepository
from app.modules.packages.models import ServicePackage, CustomerPackage, PackageSession, Installment
from app.modules.packages.schemas import PackageCreate, PackageUpdate, PackageSaleCreate, SessionComplete
from app.shared.enums.package import PackageStatus, CustomerPackageStatus, SessionStatus, InstallmentStatus
from app.shared.enums.invoice import PaymentMethod


class PackageService:
    def __init__(self, 
                 package_repo: ServicePackageRepository, 
                 customer_package_repo: CustomerPackageRepository,
                 session_repo: PackageSessionRepository,
                 installment_repo: InstallmentRepository,
                 uow: UnitOfWork):
        self.package_repo = package_repo
        self.customer_package_repo = customer_package_repo
        self.session_repo = session_repo
        self.installment_repo = installment_repo
        self.uow = uow

    def create_package(self, business_id: UUID, data: PackageCreate) -> ServicePackage:
        total_sessions = sum([s.session_count for s in data.services])
        if total_sessions <= 0:
            raise BadRequestException("Package must have at least one session")
            
        obj = ServicePackage(
            business_id=business_id,
            name=data.name,
            description=data.description,
            services=[s.model_dump(mode="json") for s in data.services],
            total_sessions=total_sessions,
            price=data.price,
            discount_percentage=data.discount_percentage,
            validity_days=data.validity_days,
            is_installment_allowed=data.is_installment_allowed,
            max_installments=data.max_installments,
            status=PackageStatus.ACTIVE
        )
        
        with self.uow:
            self.package_repo.create(obj)
            self.uow.flush()
            self.uow.refresh(obj)
            
        return obj

    def list_packages(self, business_id: UUID, page: int = 1, size: int = 20, status: Optional[PackageStatus] = None) -> list[ServicePackage]:
        return self.package_repo.list_by_business(business_id=business_id, page=page, size=size, status=status)

    def get_package(self, business_id: UUID, package_id: UUID) -> ServicePackage:
        pkg = self.package_repo.get_by_business(business_id, package_id)
        if not pkg:
            raise NotFoundException("Package not found")
        return pkg

    def update_package(self, business_id: UUID, package_id: UUID, data: PackageUpdate) -> ServicePackage:
        pkg = self.get_package(business_id, package_id)
        
        with self.uow:
            update_data = data.model_dump(exclude_unset=True)
            if "services" in update_data:
                update_data["services"] = [s for s in update_data["services"]]
                pkg.total_sessions = sum([s["session_count"] for s in update_data["services"]])
            
            self.package_repo.update(pkg, update_data)
            self.uow.flush()
            self.uow.refresh(pkg)
            
        return pkg

    def delete_package(self, business_id: UUID, package_id: UUID) -> None:
        pkg = self.get_package(business_id, package_id)
        with self.uow:
            self.package_repo.delete(pkg)
            self.uow.flush()

    def sell_package(self, business_id: UUID, data: PackageSaleCreate) -> CustomerPackage:
        pkg = self.get_package(business_id, data.package_id)
        if pkg.status != PackageStatus.ACTIVE:
            raise BadRequestException("Cannot sell an inactive package")
            
        if data.installment_count > 1 and not pkg.is_installment_allowed:
            raise BadRequestException("Installments are not allowed for this package")
            
        if data.installment_count > pkg.max_installments:
            raise BadRequestException(f"Maximum installments allowed is {pkg.max_installments}")

        with self.uow:
            now = datetime.utcnow()
            expires_at = None
            if pkg.validity_days and pkg.validity_days > 0:
                expires_at = now + timedelta(days=pkg.validity_days)
                
            discounted_price = float(pkg.price) * (1 - float(pkg.discount_percentage) / 100.0)
            
            cp = CustomerPackage(
                business_id=business_id,
                customer_id=data.customer_id,
                package_id=data.package_id,
                branch_id=data.branch_id,
                purchased_at=now,
                expires_at=expires_at,
                total_sessions=pkg.total_sessions,
                used_sessions=0,
                remaining_sessions=pkg.total_sessions,
                total_price=discounted_price,
                paid_amount=discounted_price if data.installment_count == 1 else 0.0,
                status=CustomerPackageStatus.ACTIVE,
                notes=data.notes
            )
            self.customer_package_repo.create(cp)
            self.uow.flush()
            
            # Create sessions
            session_number = 1
            for service_item in pkg.services:
                service_id_str = service_item.get("service_id")
                session_count = service_item.get("session_count", 0)
                
                service_id = UUID(service_id_str) if isinstance(service_id_str, str) else service_id_str
                
                for _ in range(session_count):
                    s = PackageSession(
                        customer_package_id=cp.id,
                        business_id=business_id,
                        service_id=service_id,
                        session_number=session_number,
                        status=SessionStatus.PENDING
                    )
                    self.session_repo.create(s)
                    session_number += 1
                    
            # Create installments
            if data.installment_count == 1:
                inst = Installment(
                    customer_package_id=cp.id,
                    business_id=business_id,
                    customer_id=data.customer_id,
                    installment_number=1,
                    amount=discounted_price,
                    due_date=now.date(),
                    paid_date=now.date(),
                    status=InstallmentStatus.PAID,
                    payment_method=data.payment_method
                )
                self.installment_repo.create(inst)
            else:
                amount_per_installment = discounted_price / data.installment_count
                for i in range(1, data.installment_count + 1):
                    due_date = now.date() + relativedelta(months=i-1)
                    inst = Installment(
                        customer_package_id=cp.id,
                        business_id=business_id,
                        customer_id=data.customer_id,
                        installment_number=i,
                        amount=amount_per_installment,
                        due_date=due_date,
                        status=InstallmentStatus.PENDING
                    )
                    self.installment_repo.create(inst)
                    
            self.uow.flush()
            self.uow.refresh(cp)
            
        return cp

    def list_customer_packages(self, business_id: UUID, page: int = 1, size: int = 20, status: Optional[CustomerPackageStatus] = None, customer_id: Optional[UUID] = None) -> list[CustomerPackage]:
        return self.customer_package_repo.list_by_business(business_id=business_id, page=page, size=size, status=status, customer_id=customer_id)

    def get_customer_package_detail(self, business_id: UUID, cp_id: UUID) -> CustomerPackage:
        cp = self.customer_package_repo.get_by_business(business_id, cp_id)
        if not cp:
            raise NotFoundException("Customer package not found")
        
        sessions = self.session_repo.list_by_customer_package(cp.id)
        installments = self.installment_repo.list_by_customer_package(cp.id)
        
        # we attach these so pydantic schema can read them
        cp.sessions = sessions
        cp.installments = installments
        return cp

    def complete_session(self, business_id: UUID, cp_id: UUID, session_id: UUID, data: SessionComplete) -> PackageSession:
        cp = self.customer_package_repo.get_by_business(business_id, cp_id)
        if not cp:
            raise NotFoundException("Customer package not found")
            
        if cp.status not in [CustomerPackageStatus.ACTIVE]:
            raise BadRequestException(f"Cannot complete session on package with status {cp.status}")
            
        session = self.session_repo.get(session_id)
        if not session or session.customer_package_id != cp.id:
            raise NotFoundException("Session not found")
            
        if session.status == SessionStatus.COMPLETED:
            raise BadRequestException("Session is already completed")
            
        with self.uow:
            session.status = SessionStatus.COMPLETED
            session.appointment_id = data.appointment_id
            session.completed_by = data.staff_id
            session.notes = data.notes
            session.session_date = datetime.utcnow()
            
            cp.used_sessions += 1
            cp.remaining_sessions = cp.total_sessions - cp.used_sessions
            
            if cp.remaining_sessions <= 0:
                cp.status = CustomerPackageStatus.COMPLETED
                
            self.uow.flush()
            self.uow.refresh(session)
            
        return session

    def cancel_session(self, business_id: UUID, cp_id: UUID, session_id: UUID) -> PackageSession:
        cp = self.customer_package_repo.get_by_business(business_id, cp_id)
        if not cp:
            raise NotFoundException("Customer package not found")
            
        session = self.session_repo.get(session_id)
        if not session or session.customer_package_id != cp.id:
            raise NotFoundException("Session not found")
            
        if session.status == SessionStatus.COMPLETED:
            raise BadRequestException("Cannot cancel a completed session")
            
        with self.uow:
            session.status = SessionStatus.CANCELLED
            self.uow.flush()
            self.uow.refresh(session)
            
        return session

    def list_installments(self, business_id: UUID, page: int = 1, size: int = 20, status: Optional[InstallmentStatus] = None) -> list[Installment]:
        return self.installment_repo.list_by_business(business_id, page, size, status)

    def list_overdue_installments(self, business_id: UUID) -> list[Installment]:
        return self.installment_repo.list_overdue(business_id)

    def pay_installment(self, business_id: UUID, installment_id: UUID, payment_method: Optional[PaymentMethod] = None) -> Installment:
        inst = self.installment_repo.get(installment_id)
        if not inst or inst.business_id != business_id:
            raise NotFoundException("Installment not found")
            
        if inst.status == InstallmentStatus.PAID:
            raise BadRequestException("Installment is already paid")
            
        cp = self.customer_package_repo.get(inst.customer_package_id)
        if not cp:
            raise NotFoundException("Customer package not found")
            
        with self.uow:
            inst.status = InstallmentStatus.PAID
            inst.paid_date = date.today()
            inst.payment_method = payment_method
            
            cp.paid_amount = float(cp.paid_amount) + float(inst.amount)
            
            self.uow.flush()
            self.uow.refresh(inst)
            
        return inst
