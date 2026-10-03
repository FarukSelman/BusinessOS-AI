from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.modules.reviews.schemas import ReviewResponse, ReviewReplyRequest, ReviewStatsResponse
from app.modules.reviews.repository import CustomerReviewRepository
from app.modules.business.repository import BusinessRepository
from app.modules.reviews.service import CustomerReviewService
from app.shared.enums.review import ReviewStatus

router = APIRouter(prefix="/businesses/{business_id}/reviews", tags=["Reviews"])

def get_service(db: Session = Depends(get_db)) -> CustomerReviewService:
    review_repo = CustomerReviewRepository(db)
    business_repo = BusinessRepository(db)
    uow = UnitOfWork(db)
    return CustomerReviewService(review_repo, business_repo, uow)

@router.get("", response_model=List[ReviewResponse])
def list_reviews(
    business_id: UUID,
    status_filter: Optional[ReviewStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: CustomerReviewService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_reviews(business_id, status_filter, page, size)

@router.get("/stats", response_model=ReviewStatsResponse)
def get_stats(
    business_id: UUID,
    service: CustomerReviewService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_stats(business_id)

@router.patch("/{review_id}/approve", response_model=ReviewResponse)
def approve_review(
    business_id: UUID,
    review_id: UUID,
    service: CustomerReviewService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.change_status(business_id, review_id, ReviewStatus.PUBLISHED)

@router.patch("/{review_id}/reject", response_model=ReviewResponse)
def reject_review(
    business_id: UUID,
    review_id: UUID,
    service: CustomerReviewService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.change_status(business_id, review_id, ReviewStatus.REJECTED)

@router.patch("/{review_id}/reply", response_model=ReviewResponse)
def reply_review(
    business_id: UUID,
    review_id: UUID,
    data: ReviewReplyRequest,
    service: CustomerReviewService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.add_reply(business_id, review_id, data)
