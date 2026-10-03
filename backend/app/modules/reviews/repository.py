from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.reviews.models import CustomerReview
from app.shared.enums.review import ReviewStatus

class CustomerReviewRepository(BaseRepository[CustomerReview]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=CustomerReview)

    def list_by_business(self, business_id: UUID, status: Optional[ReviewStatus] = None, page: int = 1, size: int = 20) -> List[CustomerReview]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        if status:
            statement = statement.where(self.model.status == status)
        
        statement = statement.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())
        
    def get_by_business(self, business_id: UUID, review_id: UUID) -> Optional[CustomerReview]:
        statement = select(self.model).where(
            self.model.id == review_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalar(statement)

    def get_stats(self, business_id: UUID) -> dict:
        stmt = select(
            func.count(self.model.id),
            func.avg(self.model.rating)
        ).where(
            self.model.business_id == business_id,
            self.model.status == ReviewStatus.PUBLISHED,
            self.model.is_deleted.is_(False)
        )
        result = self.db.execute(stmt).first()
        
        dist_stmt = select(
            self.model.rating,
            func.count(self.model.id)
        ).where(
            self.model.business_id == business_id,
            self.model.status == ReviewStatus.PUBLISHED,
            self.model.is_deleted.is_(False)
        ).group_by(self.model.rating)
        
        dist_result = self.db.execute(dist_stmt).all()
        distribution = {str(k): v for k, v in dist_result}
        for i in range(1, 6):
            if str(i) not in distribution:
                distribution[str(i)] = 0
                
        return {
            "total_count": result[0] or 0,
            "average_rating": float(result[1]) if result[1] else 0.0,
            "rating_distribution": distribution
        }
