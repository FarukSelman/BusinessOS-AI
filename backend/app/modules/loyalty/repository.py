from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.loyalty.models import LoyaltyRule, LoyaltyWallet, LoyaltyTransaction

class LoyaltyRuleRepository(BaseRepository[LoyaltyRule]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=LoyaltyRule)
        
    def get_by_business(self, business_id: UUID) -> Optional[LoyaltyRule]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalar(statement)
        
    def create_or_update(self, rule: LoyaltyRule) -> LoyaltyRule:
        existing = self.get_by_business(rule.business_id)
        if existing:
            for key, value in rule.__dict__.items():
                if not key.startswith('_'):
                    setattr(existing, key, value)
            return existing
        else:
            self.db.add(rule)
            return rule

class LoyaltyWalletRepository(BaseRepository[LoyaltyWallet]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=LoyaltyWallet)
        
    def get_by_customer(self, business_id: UUID, customer_id: UUID) -> Optional[LoyaltyWallet]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.customer_id == customer_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalar(statement)
        
    def get_by_customer_readonly(self, business_id: UUID, customer_id: UUID) -> Optional[LoyaltyWallet]:
        # Unlike LoyaltyService.get_wallet_balance this never creates a wallet.
        return self.db.scalars(select(self.model).where(
            self.model.business_id == business_id,
            self.model.customer_id == customer_id,
            self.model.is_deleted.is_(False),
        )).first()

    def get_totals(self, business_id: UUID) -> dict:
        from sqlalchemy import func
        row = self.db.execute(select(
            func.count(self.model.id), func.coalesce(func.sum(self.model.balance), 0),
            func.coalesce(func.sum(self.model.lifetime_earned), 0), func.coalesce(func.sum(self.model.lifetime_spent), 0),
        ).where(self.model.business_id == business_id, self.model.is_deleted.is_(False))).first()
        return {"wallet_count": row[0], "outstanding_points": int(row[1]), "lifetime_earned": int(row[2]), "lifetime_spent": int(row[3])}

    def list_top_by_balance(self, business_id: UUID, limit: int = 10) -> list:
        from app.modules.customers.models import Customer
        return list(self.db.execute(
            select(Customer.name, self.model.balance)
            .join(Customer, Customer.id == self.model.customer_id)
            .where(self.model.business_id == business_id, self.model.is_deleted.is_(False), self.model.balance > 0)
            .order_by(self.model.balance.desc()).limit(limit)
        ).all())

    def list_by_business(self, business_id: UUID, page: int = 1, size: int = 20) -> List[LoyaltyWallet]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())
        
    def create_wallet(self, business_id: UUID, customer_id: UUID) -> LoyaltyWallet:
        wallet = LoyaltyWallet(business_id=business_id, customer_id=customer_id)
        self.db.add(wallet)
        return wallet

class LoyaltyTransactionRepository(BaseRepository[LoyaltyTransaction]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=LoyaltyTransaction)
        
    def list_by_wallet(self, wallet_id: UUID, page: int = 1, size: int = 20) -> List[LoyaltyTransaction]:
        statement = select(self.model).where(
            self.model.wallet_id == wallet_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())
        
    def list_by_business(self, business_id: UUID, customer_id: Optional[UUID] = None, page: int = 1, size: int = 20) -> List[LoyaltyTransaction]:
        statement = select(self.model).join(LoyaltyWallet).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        if customer_id:
            statement = statement.where(LoyaltyWallet.customer_id == customer_id)
            
        statement = statement.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())
