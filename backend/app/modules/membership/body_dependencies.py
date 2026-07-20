from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser, Database
from app.core.exceptions import ForbiddenException

from app.modules.membership.models import Membership
from app.modules.membership.repository import MembershipRepository

from app.modules.user.models import User

from app.modules.invitation.schemas import InvitationCreate


def get_membership_from_invitation(
    invitation: InvitationCreate,
    db: Session = Database,
    current_user: User = CurrentUser,
) -> Membership:

    repository = MembershipRepository(db)

    membership = repository.get_by_user_and_business(
        current_user.id,
        invitation.business_id,
    )

    if membership is None:
        raise ForbiddenException(
            "You are not a member of this business."
        )

    return membership


CurrentInvitationMembership = Depends(
    get_membership_from_invitation,
)