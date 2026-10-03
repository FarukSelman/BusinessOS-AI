from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.surveys.schemas import SurveyResponseSchema, SurveySubmitResponse, SurveySubmissionResult
from app.modules.surveys.repository import SurveyRepository, SurveyResponseRepository
from app.modules.surveys.service import SurveyService

router = APIRouter(prefix="/public/surveys", tags=["Public Surveys"])

def get_service(db: Session = Depends(get_db)) -> SurveyService:
    survey_repo = SurveyRepository(db)
    response_repo = SurveyResponseRepository(db)
    uow = UnitOfWork(db)
    return SurveyService(survey_repo, response_repo, uow)

@router.get("/{survey_id}", response_model=SurveyResponseSchema)
def get_public_survey(
    survey_id: UUID,
    service: SurveyService = Depends(get_service)
):
    return service.get_public_survey(survey_id)

@router.post("/{survey_id}/respond", response_model=SurveySubmissionResult, status_code=status.HTTP_201_CREATED)
def submit_response(
    survey_id: UUID,
    data: SurveySubmitResponse,
    service: SurveyService = Depends(get_service)
):
    return service.submit_response(survey_id, data)
