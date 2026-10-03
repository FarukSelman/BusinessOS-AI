from enum import Enum

class ReminderChannel(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"

class ReminderStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"   # not sent on purpose (no e-mail, superseded by a closer reminder)
