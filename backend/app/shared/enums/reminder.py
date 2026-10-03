from enum import Enum

class ReminderChannel(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"

class ReminderStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
