from enum import Enum

class CashRegisterStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class CashTransactionType(str, Enum):
    OPENING = "OPENING"       # Açılış bakiyesi
    SALE = "SALE"             # Satış geliri
    EXPENSE = "EXPENSE"       # Gider
    DEPOSIT = "DEPOSIT"       # Para girişi
    WITHDRAWAL = "WITHDRAWAL" # Para çıkışı
    CLOSING = "CLOSING"       # Kapanış
