from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository
from app.modules.packages.models import ServicePackage, CustomerPackage, PackageSession, Installment
from app.shared.enums.package import PackageStatus, CustomerPackageStatus, SessionStatus, InstallmentStatus


class ServicePackageRepository(BaseRepository[ServicePackage]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=ServicePackage)

    def list_by_business(self, business_id: UUID, page: int = 1, size: int = 20, status: Optional[PackageStatus] = None) -> list[ServicePackage]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        if status:
            query = query.where(self.model.status == status)
            
        query = query.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())

    def get_by_business(self, business_id: UUID, package_id: UUID) -> Optional[ServicePackage]:
        return self.db.scalar(
            select(self.model).where(
                self.model.id == package_id,
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False)
            )
        )


class CustomerPackageRepository(BaseRepository[CustomerPackage]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=CustomerPackage)

    def list_by_business(self, business_id: UUID, page: int = 1, size: int = 20, status: Optional[CustomerPackageStatus] = None, customer_id: Optional[UUID] = None) -> list[CustomerPackage]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        if status:
            query = query.where(self.model.status == status)
        if customer_id:
            query = query.where(self.model.customer_id == customer_id)
            
        query = query.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())

    def list_by_customer(self, business_id: UUID, customer_id: UUID) -> list[CustomerPackage]:
        return list(self.db.scalars(
            select(self.model).where(
                self.model.business_id == business_id,
                self.model.customer_id == customer_id,
                self.model.is_deleted.is_(False)
            ).order_by(self.model.created_at.desc())
        ).all())

    def get_by_business(self, business_id: UUID, customer_package_id: UUID) -> Optional[CustomerPackage]:
        return self.db.scalar(
            select(self.model).where(
                self.model.id == customer_package_id,
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False)
            )
        )


class PackageSessionRepository(BaseRepository[PackageSession]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=PackageSession)

    def list_by_customer_package(self, customer_package_id: UUID) -> list[PackageSession]:
        return list(self.db.scalars(
            select(self.model).where(
                self.model.customer_package_id == customer_package_id,
                self.model.is_deleted.is_(False)
            ).order_by(self.model.session_number.asc())
        ).all())

    def get_pending_sessions(self, customer_package_id: UUID) -> list[PackageSession]:
        return list(self.db.scalars(
            select(self.model).where(
                self.model.customer_package_id == customer_package_id,
                self.model.status == SessionStatus.PENDING,
                self.model.is_deleted.is_(False)
            ).order_by(self.model.session_number.asc())
        ).all())


class InstallmentRepository(BaseRepository[Installment]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Installment)

    def list_by_customer_package(self, customer_package_id: UUID) -> list[Installment]:
        return list(self.db.scalars(
            select(self.model).where(
                self.model.customer_package_id == customer_package_id,
                self.model.is_deleted.is_(False)
            ).order_by(self.model.installment_number.asc())
        ).all())

    def list_overdue(self, business_id: UUID) -> list[Installment]:
        today = date.today()
        return list(self.db.scalars(
            select(self.model).where(
                self.model.business_id == business_id,
                self.model.status == InstallmentStatus.PENDING,
                self.model.due_date < today,
                self.model.is_deleted.is_(False)
            ).order_by(self.model.due_date.asc())
        ).all())

    def list_by_business(self, business_id: UUID, page: int = 1, size: int = 20, status: Optional[InstallmentStatus] = None) -> list[Installment]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        if status:
            query = query.where(self.model.status == status)
            
        query = query.order_by(self.model.due_date.asc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())
