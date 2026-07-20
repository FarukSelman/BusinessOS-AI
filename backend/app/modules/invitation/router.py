from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.invitation.repository import InvitationRepository
from app.modules.invitation.schemas import (
    InvitationCreate,
    InvitationResponse,
)
from app.modules.invitation.service import InvitationService

from app.modules.membership.repository import MembershipRepository
from app.modules.user.models import User

from app.shared.security.business import require_owner


# ==========================================================
# Business Invitations
# ==========================================================

router = APIRouter(
    prefix="/businesses/{business_id}/invitations",
    tags=["Invitations"],
)


# ==========================================================
# Dependency
# ==========================================================

def get_service(
    db: Session = Depends(get_db),
) -> InvitationService:

    invitation_repository = InvitationRepository(db)

    membership_repository = MembershipRepository(db)

    uow = UnitOfWork(db)

    return InvitationService(
        repository=invitation_repository,
        membership_repository=membership_repository,
        uow=uow,
    )


# ==========================================================
# CREATE INVITATION
# ==========================================================

@router.post(
    "",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invitation",
)
def create_invitation(
    business_id: UUID,

    data: InvitationCreate,

    service: InvitationService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_owner,
    ),
):

    return service.create_invitation(
        business_id=business_id,
        data=data,
    )


# ==========================================================
# LIST BUSINESS INVITATIONS
# ==========================================================

@router.get(
    "",
    response_model=list[InvitationResponse],
    summary="List business invitations",
)
def list_business_invitations(
    business_id: UUID,

    page: int = 1,
    size: int = 20,

    service: InvitationService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_owner,
    ),
):

    return service.get_business_invitations(
        business_id=business_id,
        page=page,
        size=size,
    )