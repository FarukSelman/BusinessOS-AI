from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.shared.enums.business import BusinessStatus
from app.shared.enums.business_plan import BusinessPlan


class AdminBusinessResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    industry: str
    email: str
    phone: str
    status: BusinessStatus
    plan: BusinessPlan
    member_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminBusinessStatusUpdate(BaseModel):
    status: BusinessStatus


class AdminBusinessPlanUpdate(BaseModel):
    plan: BusinessPlan


class AdminUserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    is_superadmin: bool
    created_at: datetime

    class Config:
        from_attributes = True