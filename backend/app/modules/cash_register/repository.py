from uuid import UUID
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.cash_register.models import CashRegister, CashTransaction
from app.shared.enums.cash_register import CashRegisterStatus

class CashRegisterRepository(BaseRepository[CashRegister]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=CashRegister)

    def get_open_register(self, business_id: UUID, branch_id: UUID | None = None) -> CashRegister | None:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.status == CashRegisterStatus.OPEN,
            self.model.is_deleted.is_(False)
        )
        if branch_id:
            query = query.where(self.model.branch_id == branch_id)
        return self.db.scalars(query).first()

    def get_by_date(self, business_id: UUID, register_date: date, branch_id: UUID | None = None) -> CashRegister | None:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.register_date == register_date,
            self.model.is_deleted.is_(False)
        )
        if branch_id:
            query = query.where(self.model.branch_id == branch_id)
        return self.db.scalars(query).first()

    def list_by_business(self, business_id: UUID, page: int = 1, size: int = 20) -> list[CashRegister]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.register_date.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())

class CashTransactionRepository(BaseRepository[CashTransaction]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=CashTransaction)

    def list_by_register(self, register_id: UUID) -> list[CashTransaction]:
        query = select(self.model).where(
            self.model.register_id == register_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.created_at)
        return list(self.db.scalars(query).all())
