from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.surveys.models import Survey, SurveyResponseModel
from app.shared.enums.survey import SurveyStatus

class SurveyRepository(BaseRepository[Survey]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Survey)

    def list_by_business(self, business_id: UUID, page: int = 1, size: int = 20) -> List[Survey]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())
        
    def get_by_business(self, business_id: UUID, survey_id: UUID) -> Optional[Survey]:
        statement = select(self.model).where(
            self.model.id == survey_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalar(statement)
        
    def get_public_survey(self, survey_id: UUID) -> Optional[Survey]:
        statement = select(self.model).where(
            self.model.id == survey_id,
            self.model.status == SurveyStatus.ACTIVE,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalar(statement)

class SurveyResponseRepository(BaseRepository[SurveyResponseModel]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=SurveyResponseModel)

    def list_by_survey(self, survey_id: UUID, page: int = 1, size: int = 20) -> List[SurveyResponseModel]:
        statement = select(self.model).where(
            self.model.survey_id == survey_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())

    def get_stats(self, survey_id: UUID) -> dict:
        stmt = select(
            func.count(self.model.id),
            func.avg(self.model.overall_rating)
        ).where(
            self.model.survey_id == survey_id,
            self.model.is_deleted.is_(False)
        )
        result = self.db.execute(stmt).first()
        return {
            "response_count": result[0] or 0,
            "average_rating": float(result[1]) if result[1] else 0.0
        }
