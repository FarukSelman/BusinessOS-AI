from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any, Dict
from uuid import UUID
from datetime import datetime
from app.shared.enums.survey import SurveyStatus, QuestionType

class QuestionSchema(BaseModel):
    id: str
    type: QuestionType
    text: str
    options: Optional[List[str]] = None
    required: bool = False

class SurveyCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    questions: List[QuestionSchema]
    status: SurveyStatus = SurveyStatus.DRAFT
    is_auto_send: bool = False

class SurveyUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    questions: Optional[List[QuestionSchema]] = None
    status: Optional[SurveyStatus] = None
    is_auto_send: Optional[bool] = None

class SurveyResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    title: str
    description: Optional[str] = None
    questions: List[Dict[str, Any]]
    status: SurveyStatus
    is_auto_send: bool
    created_at: datetime
    updated_at: datetime

class AnswerSchema(BaseModel):
    question_id: str
    answer: Any

class SurveySubmitResponse(BaseModel):
    customer_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None
    answers: List[AnswerSchema]
    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    respondent_name: Optional[str] = None
    respondent_email: Optional[str] = None

class SurveySubmissionResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    survey_id: UUID
    created_at: datetime
