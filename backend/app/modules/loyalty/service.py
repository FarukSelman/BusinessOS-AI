from uuid import UUID
from typing import List, Optional
from app.db.unit_of_work import UnitOfWork
from app.core.exceptions import NotFoundException, BadRequestException
from app.modules.loyalty.models import LoyaltyRule, LoyaltyWallet, LoyaltyTransaction
from app.modules.loyalty.repository import LoyaltyRuleRepository, LoyaltyWalletRepository, LoyaltyTransactionRepository
from app.modules.loyalty.schemas import LoyaltyRuleCreate, LoyaltyRuleUpdate
from app.shared.enums.loyalty import TransactionType, WalletStatus

class LoyaltyService:
    def __init__(self, rule_repository: LoyaltyRuleRepository, wallet_repository: LoyaltyWalletRepository, transaction_repository: LoyaltyTransactionRepository, uow: UnitOfWork):
        self.rule_repository = rule_repository
        self.wallet_repository = wallet_repository
        self.transaction_repository = transaction_repository
        self.uow = uow

    def get_or_create_rule(self, business_id: UUID) -> LoyaltyRule:
        rule = self.rule_repository.get_by_business(business_id)
        if not rule:
            rule = LoyaltyRule(business_id=business_id)
            with self.uow:
                self.rule_repository.create_or_update(rule)
                self.uow.flush()
                self.uow.refresh(rule)
        return rule

    def update_rule(self, business_id: UUID, data: LoyaltyRuleUpdate) -> LoyaltyRule:
        rule = self.get_or_create_rule(business_id)
        with self.uow:
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(rule, key, value)
            self.uow.flush()
            self.uow.refresh(rule)
        return rule

    def get_or_create_wallet(self, business_id: UUID, customer_id: UUID) -> LoyaltyWallet:
        wallet = self.wallet_repository.get_by_customer(business_id, customer_id)
        if not wallet:
            wallet = self.wallet_repository.create_wallet(business_id, customer_id)
            with self.uow:
                self.uow.flush()
                self.uow.refresh(wallet)
        return wallet

    def earn_points(self, business_id: UUID, customer_id: UUID, points: int, description: Optional[str] = None, reference_type: Optional[str] = None, reference_id: Optional[UUID] = None) -> LoyaltyTransaction:
        if points <= 0:
            raise BadRequestException("Points must be positive")
        
        wallet = self.get_or_create_wallet(business_id, customer_id)
        
        transaction = LoyaltyTransaction(
            wallet_id=wallet.id,
            business_id=business_id,
            transaction_type=TransactionType.EARN,
            points=points,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id
        )
        
        with self.uow:
            wallet.balance += points
            wallet.lifetime_earned += points
            self.transaction_repository.create(transaction)
            self.uow.flush()
            self.uow.refresh(transaction)
            
        return transaction

    def spend_points(self, business_id: UUID, customer_id: UUID, points: int, description: Optional[str] = None, reference_type: Optional[str] = None, reference_id: Optional[UUID] = None) -> LoyaltyTransaction:
        if points <= 0:
            raise BadRequestException("Points must be positive")
            
        wallet = self.get_or_create_wallet(business_id, customer_id)
        
        if wallet.balance < points:
            raise BadRequestException("Insufficient balance")
            
        transaction = LoyaltyTransaction(
            wallet_id=wallet.id,
            business_id=business_id,
            transaction_type=TransactionType.SPEND,
            points=points,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id
        )
        
        with self.uow:
            wallet.balance -= points
            wallet.lifetime_spent += points
            self.transaction_repository.create(transaction)
            self.uow.flush()
            self.uow.refresh(transaction)
            
        return transaction

    def adjust_points(self, business_id: UUID, customer_id: UUID, points: int, description: Optional[str] = None) -> LoyaltyTransaction:
        wallet = self.get_or_create_wallet(business_id, customer_id)
        
        transaction = LoyaltyTransaction(
            wallet_id=wallet.id,
            business_id=business_id,
            transaction_type=TransactionType.ADJUSTMENT,
            points=points,
            description=description
        )
        
        with self.uow:
            wallet.balance += points
            if points > 0:
                wallet.lifetime_earned += points
            self.transaction_repository.create(transaction)
            self.uow.flush()
            self.uow.refresh(transaction)
            
        return transaction

    def get_wallet_balance(self, business_id: UUID, customer_id: UUID) -> LoyaltyWallet:
        return self.get_or_create_wallet(business_id, customer_id)

    def list_transactions(self, business_id: UUID, customer_id: Optional[UUID] = None, page: int = 1, size: int = 20) -> List[LoyaltyTransaction]:
        return self.transaction_repository.list_by_business(business_id, customer_id, page, size)

    def list_wallets(self, business_id: UUID, page: int = 1, size: int = 20) -> List[LoyaltyWallet]:
        return self.wallet_repository.list_by_business(business_id, page, size)
