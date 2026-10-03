from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.shared.enums.review import ReviewStatus

class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    customer_id: Optional[UUID]
    appointment_id: Optional[UUID]
    service_id: Optional[UUID]
    rating: int
    comment: Optional[str]
    reviewer_name: str
    status: ReviewStatus
    reply: Optional[str]
    replied_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class ReviewSubmitRequest(BaseModel):
    customer_id: Optional[UUID] = None
    reviewer_name: str = Field(..., max_length=150)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    service_id: Optional[UUID] = None
    appointment_id: Optional[UUID] = None

class ReviewReplyRequest(BaseModel):
    reply: str

class ReviewStatsResponse(BaseModel):
    average_rating: float
    total_count: int
    rating_distribution: dict
