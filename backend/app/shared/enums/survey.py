from enum import Enum

class SurveyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DRAFT = "DRAFT"

class QuestionType(str, Enum):
    RATING = "RATING"
    TEXT = "TEXT"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    YES_NO = "YES_NO"
