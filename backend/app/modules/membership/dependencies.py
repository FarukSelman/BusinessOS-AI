from uuid import UUID

from sqlalchemy.orm import Session

from app.core.dependencies import (
    Database,
    CurrentUser,
)

from app.core.exceptions import (
    ForbiddenException,
)

from app.modules.membership.models import Membership
from app.modules.membership.repository import MembershipRepository

from app.modules.user.models import User


def get_current_membership(
    business_id: UUID,
    db: Session = Database,
    current_user: User = CurrentUser,
) -> Membership:

    repository = MembershipRepository(db)

    membership = repository.get_by_user_and_business(
        current_user.id,
        business_id,
    )

    if membership is None:

        raise ForbiddenException(
            "You are not a member of this business."
        )

    return membership