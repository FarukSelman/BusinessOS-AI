from uuid import UUID
from typing import List
from app.db.unit_of_work import UnitOfWork
from app.core.exceptions import NotFoundException
from app.modules.surveys.models import Survey, SurveyResponseModel
from app.modules.surveys.repository import SurveyRepository, SurveyResponseRepository
from app.modules.surveys.schemas import SurveyCreate, SurveyUpdate, SurveySubmitResponse

class SurveyService:
    def __init__(self, survey_repository: SurveyRepository, response_repository: SurveyResponseRepository, uow: UnitOfWork):
        self.survey_repository = survey_repository
        self.response_repository = response_repository
        self.uow = uow

    def create_survey(self, business_id: UUID, data: SurveyCreate) -> Survey:
        survey = Survey(
            business_id=business_id,
            title=data.title,
            description=data.description,
            questions=[q.model_dump() for q in data.questions],
            status=data.status,
            is_auto_send=data.is_auto_send
        )
        with self.uow:
            self.survey_repository.create(survey)
            self.uow.flush()
            self.uow.refresh(survey)
        return survey

    def list_surveys(self, business_id: UUID, page: int = 1, size: int = 20) -> List[Survey]:
        return self.survey_repository.list_by_business(business_id, page, size)

    def get_survey(self, business_id: UUID, survey_id: UUID) -> Survey:
        survey = self.survey_repository.get_by_business(business_id, survey_id)
        if not survey:
            raise NotFoundException("Survey not found")
        return survey

    def update_survey(self, business_id: UUID, survey_id: UUID, data: SurveyUpdate) -> Survey:
        survey = self.get_survey(business_id, survey_id)
        with self.uow:
            dump = data.model_dump(exclude_unset=True)
            if 'questions' in dump:
                dump['questions'] = [q for q in dump['questions']]
            for key, value in dump.items():
                setattr(survey, key, value)
            self.uow.flush()
            self.uow.refresh(survey)
        return survey

    def delete_survey(self, business_id: UUID, survey_id: UUID):
        survey = self.get_survey(business_id, survey_id)
        with self.uow:
            self.survey_repository.soft_delete(survey_id)

    def list_responses(self, business_id: UUID, survey_id: UUID, page: int = 1, size: int = 20) -> List[SurveyResponseModel]:
        # Validate survey belongs to business
        self.get_survey(business_id, survey_id)
        return self.response_repository.list_by_survey(survey_id, page, size)

    def get_stats(self, business_id: UUID, survey_id: UUID) -> dict:
        self.get_survey(business_id, survey_id)
        return self.response_repository.get_stats(survey_id)

    def get_public_survey(self, survey_id: UUID) -> Survey:
        survey = self.survey_repository.get_public_survey(survey_id)
        if not survey:
            raise NotFoundException("Survey not found or not active")
        return survey

    def submit_response(self, survey_id: UUID, data: SurveySubmitResponse) -> SurveyResponseModel:
        survey = self.get_public_survey(survey_id)
        
        response = SurveyResponseModel(
            survey_id=survey_id,
            business_id=survey.business_id,
            customer_id=data.customer_id,
            appointment_id=data.appointment_id,
            answers=[a.model_dump() for a in data.answers],
            overall_rating=data.overall_rating,
            comment=data.comment,
            respondent_name=data.respondent_name,
            respondent_email=data.respondent_email
        )
        with self.uow:
            self.response_repository.create(response)
            self.uow.flush()
            self.uow.refresh(response)
        return response
