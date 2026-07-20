from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.invitation.repository import InvitationRepository
from app.modules.invitation.schemas import InvitationResponse
from app.modules.invitation.service import InvitationService

from app.modules.membership.repository import MembershipRepository
from app.modules.user.models import User

from app.shared.security.dependencies import get_current_user


router = APIRouter(
    prefix="/invitations",
    tags=["Invitations"],
)


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


@router.post(
    "/accept/{token}",
    response_model=InvitationResponse,
    summary="Accept invitation",
)
def accept_invitation(
    token: str,

    service: InvitationService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.accept_invitation(
        token=token,
        user_id=current_user.id,
    )