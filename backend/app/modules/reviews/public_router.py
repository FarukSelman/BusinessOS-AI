from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.reviews.schemas import ReviewResponse, ReviewSubmitRequest
from app.modules.reviews.repository import CustomerReviewRepository
from app.modules.business.repository import BusinessRepository
from app.modules.reviews.service import CustomerReviewService

router = APIRouter(prefix="/public/reviews", tags=["Public Reviews"])

def get_service(db: Session = Depends(get_db)) -> CustomerReviewService:
    review_repo = CustomerReviewRepository(db)
    business_repo = BusinessRepository(db)
    uow = UnitOfWork(db)
    return CustomerReviewService(review_repo, business_repo, uow)

@router.get("/{business_slug}", response_model=List[ReviewResponse])
def get_public_reviews(
    business_slug: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: CustomerReviewService = Depends(get_service)
):
    return service.get_public_reviews(business_slug, page, size)

@router.post("/{business_slug}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def submit_review(
    business_slug: str,
    data: ReviewSubmitRequest,
    service: CustomerReviewService = Depends(get_service)
):
    return service.submit_review(business_slug, data)
