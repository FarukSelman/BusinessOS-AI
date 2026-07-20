from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.shared.enums.invitation import InvitationStatus
from app.shared.enums.membership import MembershipRole


# ==========================================================
# CREATE INVITATION
# ==========================================================

class InvitationCreate(BaseModel):
    email: EmailStr
    role: MembershipRole = MembershipRole.EMPLOYEE


# ==========================================================
# ACCEPT INVITATION
# ==========================================================

class InvitationAccept(BaseModel):
    token: str


# ==========================================================
# BUSINESS MINI RESPONSE
# ==========================================================

class InvitationBusinessResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    name: str
    slug: str


# ==========================================================
# INVITATION RESPONSE
# ==========================================================

class InvitationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    business_id: UUID

    email: EmailStr

    role: MembershipRole

    token: str

    status: InvitationStatus

    expires_at: datetime

    accepted_at: datetime | None

    created_at: datetime

    updated_at: datetime

    business: InvitationBusinessResponse