from enum import Enum

class BlockType(str, Enum):
    FULL_DAY = "FULL_DAY"       # Tüm gün kapalı
    TIME_RANGE = "TIME_RANGE"   # Belirli saat aralığı kapalı
    RECURRING = "RECURRING"     # Tekrarlayan blok (her hafta belirli gün)

class RecurrenceDay(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"
