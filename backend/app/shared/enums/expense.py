from enum import Enum

class TransactionDirection(str, Enum):
    INCOME = "INCOME"     # Gelir
    EXPENSE = "EXPENSE"   # Gider

class ExpenseStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

class RecurrenceType(str, Enum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
