from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.modules.invitation.repository import InvitationRepository
from app.modules.invitation.schemas import (
    InvitationCreate,
    InvitationResponse,
)
from app.modules.invitation.service import InvitationService

from app.modules.membership.repository import MembershipRepository

from app.modules.user.models import User

from app.shared.security.dependencies import (
    get_current_user,
)

router = APIRouter(
    prefix="/invitations",
    tags=["Invitations"],
)


def get_service(
    db: Session = Depends(get_db),
):
    repository = InvitationRepository(db)

    membership_repository = MembershipRepository(db)

    return InvitationService(
        repository,
        membership_repository,
    )


@router.post(
    "",
    response_model=InvitationResponse,
)
def create_invitation(
    invitation: InvitationCreate,
    service: InvitationService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    return service.create_invitation(
        invitation
    )


@router.get(
    "/business/{business_id}",
    response_model=list[InvitationResponse],
)
def get_business_invitations(
    business_id: UUID,
    service: InvitationService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    return service.get_business_invitations(
        business_id
    )


@router.get(
    "/{token}",
    response_model=InvitationResponse,
)
def get_invitation(
    token: str,
    service: InvitationService = Depends(get_service),
):
    return service.get_invitation_by_token(
        token
    )


@router.post(
    "/accept/{token}",
    response_model=InvitationResponse,
)
def accept_invitation(
    token: str,
    service: InvitationService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    return service.accept_invitation(
        token,
        current_user.id,
    )