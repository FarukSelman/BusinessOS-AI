from uuid import UUID
from datetime import date, datetime, timezone
from app.db.unit_of_work import UnitOfWork
from app.modules.cash_register.repository import CashRegisterRepository, CashTransactionRepository
from app.modules.cash_register.models import CashRegister, CashTransaction
from app.modules.cash_register.schemas import CashRegisterOpen, CashRegisterClose, CashTransactionCreate, RegisterSummary
from app.core.exceptions import NotFoundException, BadRequestException
from app.shared.enums.cash_register import CashRegisterStatus, CashTransactionType

class CashRegisterService:
    def __init__(self, register_repo: CashRegisterRepository, transaction_repo: CashTransactionRepository, uow: UnitOfWork):
        self.register_repo = register_repo
        self.transaction_repo = transaction_repo
        self.uow = uow

    def open_register(self, business_id: UUID, data: CashRegisterOpen, user_id: UUID | None = None) -> CashRegister:
        today = date.today()
        existing = self.register_repo.get_by_date(business_id, today, data.branch_id)
        if existing and existing.status == CashRegisterStatus.OPEN:
            raise BadRequestException("Bugün için zaten açık bir kasa mevcut.")
        
        # Auto-close any stale open registers from previous days
        open_reg = self.register_repo.get_open_register(business_id, data.branch_id)
        if open_reg:
            if open_reg.register_date < today:
                # Stale register — close it automatically
                open_reg.status = CashRegisterStatus.CLOSED
                open_reg.closed_at = datetime.now(timezone.utc)
                open_reg.closing_balance = open_reg.opening_balance
                open_reg.notes = (open_reg.notes or "") + " [Otomatik kapatıldı]"
            else:
                raise BadRequestException("Zaten açık bir kasa var. Lütfen önce kapatın.")

        obj = CashRegister(
            business_id=business_id,
            branch_id=data.branch_id,
            opened_by=user_id,
            register_date=today,
            opening_balance=data.opening_balance,
            status=CashRegisterStatus.OPEN,
            opened_at=datetime.now(timezone.utc),
            notes=data.notes
        )
        
        with self.uow:
            self.register_repo.create(obj)
            self.uow.flush()
            
            # Initial opening transaction
            if data.opening_balance > 0:
                tx = CashTransaction(
                    register_id=obj.id,
                    business_id=business_id,
                    transaction_type=CashTransactionType.OPENING,
                    amount=data.opening_balance,
                    description="Opening Balance",
                    created_by=user_id
                )
                self.transaction_repo.create(tx)
            
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def close_register(self, business_id: UUID, register_id: UUID, data: CashRegisterClose, user_id: UUID | None = None) -> CashRegister:
        obj = self.register_repo.get_by_id(register_id)
        if not obj or obj.business_id != business_id:
            raise NotFoundException("Kasa bulunamadı.")
        if obj.status == CashRegisterStatus.CLOSED:
            raise BadRequestException("Kasa zaten kapalı.")

        summary = self.get_register_summary(register_id)
        expected = summary.expected_closing

        with self.uow:
            obj.closing_balance = data.closing_balance
            obj.expected_balance = expected
            obj.difference = data.closing_balance - expected
            obj.status = CashRegisterStatus.CLOSED
            obj.closed_by = user_id
            obj.closed_at = datetime.now(timezone.utc)
            if data.notes:
                obj.notes = data.notes
            
            tx = CashTransaction(
                register_id=obj.id,
                business_id=business_id,
                transaction_type=CashTransactionType.CLOSING,
                amount=data.closing_balance,
                description="Closing Balance",
                created_by=user_id
            )
            self.transaction_repo.create(tx)
            
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def add_transaction(self, business_id: UUID, register_id: UUID, data: CashTransactionCreate, user_id: UUID | None = None) -> CashTransaction:
        reg = self.register_repo.get_by_id(register_id)
        if not reg or reg.business_id != business_id:
            raise NotFoundException("Kasa bulunamadı.")
        if reg.status == CashRegisterStatus.CLOSED:
            raise BadRequestException("Kapalı kasaya işlem eklenemez.")

        obj = CashTransaction(
            register_id=register_id,
            business_id=business_id,
            transaction_type=data.transaction_type,
            amount=data.amount,
            description=data.description,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            created_by=user_id
        )
        with self.uow:
            self.transaction_repo.create(obj)
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def get_register(self, business_id: UUID, register_id: UUID) -> CashRegister:
        reg = self.register_repo.get_by_id(register_id)
        if not reg or reg.business_id != business_id:
            raise NotFoundException("Kasa bulunamadı.")
        return reg

    def get_register_summary(self, register_id: UUID, business_id: UUID | None = None) -> RegisterSummary:
        if business_id is not None:
            self.get_register(business_id, register_id)
        transactions = self.transaction_repo.list_by_register(register_id)
        opening = sum([t.amount for t in transactions if t.transaction_type == CashTransactionType.OPENING])
        sales = sum([t.amount for t in transactions if t.transaction_type == CashTransactionType.SALE])
        deposits = sum([t.amount for t in transactions if t.transaction_type == CashTransactionType.DEPOSIT])
        expenses = sum([t.amount for t in transactions if t.transaction_type == CashTransactionType.EXPENSE])
        withdrawals = sum([t.amount for t in transactions if t.transaction_type == CashTransactionType.WITHDRAWAL])
        
        expected = (opening + sales + deposits) - (expenses + withdrawals)
        return RegisterSummary(
            opening_balance=float(opening),
            total_sales=float(sales),
            total_expenses=float(expenses),
            total_deposits=float(deposits),
            total_withdrawals=float(withdrawals),
            expected_closing=float(expected)
        )
