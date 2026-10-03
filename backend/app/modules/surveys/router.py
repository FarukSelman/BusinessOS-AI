from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.modules.surveys.schemas import SurveyCreate, SurveyUpdate, SurveyResponseSchema
from app.modules.surveys.repository import SurveyRepository, SurveyResponseRepository
from app.modules.surveys.service import SurveyService
from app.shared.security.business import require_business_member

router = APIRouter(prefix="/businesses/{business_id}/surveys", tags=["Surveys"], dependencies=[Depends(require_business_member)])

def get_service(db: Session = Depends(get_db)) -> SurveyService:
    survey_repo = SurveyRepository(db)
    response_repo = SurveyResponseRepository(db)
    uow = UnitOfWork(db)
    return SurveyService(survey_repo, response_repo, uow)

@router.post("", response_model=SurveyResponseSchema, status_code=status.HTTP_201_CREATED)
def create_survey(
    business_id: UUID,
    data: SurveyCreate,
    service: SurveyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.create_survey(business_id, data)

@router.get("", response_model=List[SurveyResponseSchema])
def list_surveys(
    business_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: SurveyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_surveys(business_id, page, size)

@router.get("/{survey_id}", response_model=SurveyResponseSchema)
def get_survey(
    business_id: UUID,
    survey_id: UUID,
    service: SurveyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_survey(business_id, survey_id)

@router.patch("/{survey_id}", response_model=SurveyResponseSchema)
def update_survey(
    business_id: UUID,
    survey_id: UUID,
    data: SurveyUpdate,
    service: SurveyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.update_survey(business_id, survey_id, data)

@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_survey(
    business_id: UUID,
    survey_id: UUID,
    service: SurveyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    service.delete_survey(business_id, survey_id)

@router.get("/{survey_id}/responses")
def list_responses(
    business_id: UUID,
    survey_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: SurveyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    responses = service.list_responses(business_id, survey_id, page, size)
    return [
        {
            "id": r.id,
            "survey_id": r.survey_id,
            "business_id": r.business_id,
            "customer_id": r.customer_id,
            "appointment_id": r.appointment_id,
            "answers": r.answers,
            "overall_rating": r.overall_rating,
            "comment": r.comment,
            "respondent_name": r.respondent_name,
            "respondent_email": r.respondent_email,
            "created_at": r.created_at
        } for r in responses
    ]

@router.get("/{survey_id}/stats")
def get_stats(
    business_id: UUID,
    survey_id: UUID,
    service: SurveyService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_stats(business_id, survey_id)
