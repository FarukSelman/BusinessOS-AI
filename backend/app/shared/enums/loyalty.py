from enum import Enum

class TransactionType(str, Enum):
    EARN = "EARN"
    SPEND = "SPEND"
    EXPIRE = "EXPIRE"
    ADJUSTMENT = "ADJUSTMENT"
    BONUS = "BONUS"

class WalletStatus(str, Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
