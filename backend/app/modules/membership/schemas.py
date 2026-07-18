from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.shared.enums.membership import MembershipRole


# -----------------------
# User Mini
# -----------------------

class UserMiniResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    first_name: str
    last_name: str
    email: str


# -----------------------
# Business Mini
# -----------------------

class BusinessMiniResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    name: str
    slug: str


# -----------------------
# Create
# -----------------------

class MembershipCreate(BaseModel):
    user_id: UUID
    business_id: UUID
    role: MembershipRole = MembershipRole.EMPLOYEE


# -----------------------
# Response
# -----------------------

class MembershipResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    role: MembershipRole

    user: UserMiniResponse

    business: BusinessMiniResponse

    created_at: datetime

    updated_at: datetime