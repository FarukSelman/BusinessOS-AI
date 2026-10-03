from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone
from app.db.unit_of_work import UnitOfWork
from app.core.exceptions import NotFoundException
from app.modules.reviews.models import CustomerReview
from app.modules.reviews.repository import CustomerReviewRepository
from app.modules.reviews.schemas import ReviewSubmitRequest, ReviewReplyRequest
from app.shared.enums.review import ReviewStatus
from app.modules.business.repository import BusinessRepository

class CustomerReviewService:
    def __init__(self, review_repository: CustomerReviewRepository, business_repository: BusinessRepository, uow: UnitOfWork):
        self.review_repository = review_repository
        self.business_repository = business_repository
        self.uow = uow

    def list_reviews(self, business_id: UUID, status: Optional[ReviewStatus] = None, page: int = 1, size: int = 20) -> List[CustomerReview]:
        return self.review_repository.list_by_business(business_id, status, page, size)

    def get_stats(self, business_id: UUID) -> dict:
        return self.review_repository.get_stats(business_id)

    def change_status(self, business_id: UUID, review_id: UUID, status: ReviewStatus) -> CustomerReview:
        review = self.review_repository.get_by_business(business_id, review_id)
        if not review:
            raise NotFoundException("Review not found")
            
        with self.uow:
            review.status = status
            self.uow.flush()
            self.uow.refresh(review)
        return review

    def add_reply(self, business_id: UUID, review_id: UUID, data: ReviewReplyRequest) -> CustomerReview:
        review = self.review_repository.get_by_business(business_id, review_id)
        if not review:
            raise NotFoundException("Review not found")
            
        with self.uow:
            review.reply = data.reply
            review.replied_at = datetime.now(timezone.utc)
            self.uow.flush()
            self.uow.refresh(review)
        return review

    def submit_review(self, business_slug: str, data: ReviewSubmitRequest) -> CustomerReview:
        business = self.business_repository.get_by_slug(business_slug)
        if not business:
            raise NotFoundException("Business not found")
            
        review = CustomerReview(
            business_id=business.id,
            customer_id=data.customer_id,
            reviewer_name=data.reviewer_name,
            rating=data.rating,
            comment=data.comment,
            service_id=data.service_id,
            appointment_id=data.appointment_id
        )
        with self.uow:
            self.review_repository.create(review)
            self.uow.flush()
            self.uow.refresh(review)
        return review

    def get_public_reviews(self, business_slug: str, page: int = 1, size: int = 20) -> List[CustomerReview]:
        business = self.business_repository.get_by_slug(business_slug)
        if not business:
            raise NotFoundException("Business not found")
            
        return self.review_repository.list_by_business(business.id, ReviewStatus.PUBLISHED, page, size)
