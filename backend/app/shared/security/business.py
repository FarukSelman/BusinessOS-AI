"""
Business-scoped authorization.

Every endpoint under /businesses/{business_id}/... must prove that the current
user is a member of *that* business. All checks below go through one
dependency, get_business_membership, so there is a single place that decides
membership. Role checks build on top of it:

    require_business_member  -> any member (OWNER, ADMIN, EMPLOYEE, VIEWER)
    require_permission(p)    -> member whose role has permission p
                                (see app/shared/security/permissions.py)
    require_admin            -> OWNER or ADMIN
    require_owner            -> OWNER

FastAPI caches dependencies per request, so stacking these on a router and an
endpoint performs the membership lookup only once.
"""

from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException
from app.db.session import get_db
from app.modules.membership.models import Membership
from app.modules.membership.repository import MembershipRepository
from app.modules.user.models import User
from app.shared.enums.membership import MembershipRole
from app.shared.security.dependencies import get_current_user


# ---------------------------------------------------------
# Core: membership of the business in the path
# ---------------------------------------------------------

def get_business_membership(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Membership:
    """
    Returns the current user's membership in the business from the URL path.
    Raises 403 when the user is not a member.
    """

    membership = MembershipRepository(db).get_by_user_and_business(
        user_id=current_user.id,
        business_id=business_id,
    )

    if membership is None:
        raise ForbiddenException(
            "You are not a member of this business.",
        )

    return membership


# ---------------------------------------------------------
# Any member
# ---------------------------------------------------------

def require_business_member(
    membership: Membership = Depends(get_business_membership),
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


# Backwards-compatible name used by existing routers.
require_member = require_business_member


# ---------------------------------------------------------
# Role helpers
# ---------------------------------------------------------

def _require_roles(*roles: MembershipRole, message: str):

    def checker(
        membership: Membership = Depends(get_business_membership),
        current_user: User = Depends(get_current_user),
    ) -> User:
        if membership.role not in roles:
            raise ForbiddenException(message)
        return current_user

    return checker


require_admin = _require_roles(
    MembershipRole.OWNER,
    MembershipRole.ADMIN,
    message="Only business admins can perform this action.",
)

require_owner = _require_roles(
    MembershipRole.OWNER,
    message="Only business owners can perform this action.",
)
