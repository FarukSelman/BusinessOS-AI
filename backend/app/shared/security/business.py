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
    require_finance          -> roles that may see money (can_view_finance)
    require_staff            -> OWNER, ADMIN or EMPLOYEE (everyone but VIEWER)

FastAPI caches dependencies per request, so stacking these on a router and an
endpoint performs the membership lookup only once.

VIEWER is read-only, and that rule also lives in get_business_membership: a
viewer's write request (anything but GET/HEAD/OPTIONS) is refused unless the
route is marked @viewer_allowed. New write routes are therefore closed to
viewers by default. Routes outside /businesses/{business_id} (login,
register, own profile and password, public pages) never reach this check.
"""

from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException
from app.db.session import get_db
from app.modules.membership.models import Membership
from app.modules.membership.repository import MembershipRepository
from app.modules.user.models import User
from app.shared.enums.membership import MembershipRole
from app.shared.security.dependencies import get_current_user


STAFF_ONLY = "İzleyici rolü değişiklik yapamaz."

READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def viewer_allowed(endpoint):
    """
    Marks a business route a VIEWER may call with a write method: asking the
    AI or the knowledge base, deleting their own chat history. Put it under
    the @router.<method>(...) decorator.
    """
    endpoint.viewer_allowed = True
    return endpoint


# ---------------------------------------------------------
# Core: membership of the business in the path
# ---------------------------------------------------------

def get_business_membership(
    business_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Membership:
    """
    Returns the current user's membership in the business from the URL path.
    Raises 403 when the user is not a member, or is a VIEWER sending a write
    request to a route not marked @viewer_allowed.
    """

    membership = MembershipRepository(db).get_by_user_and_business(
        user_id=current_user.id,
        business_id=business_id,
    )

    if membership is None:
        raise ForbiddenException(
            "Bu işletmenin üyesi değilsiniz.",
        )

    if (
        membership.role == MembershipRole.VIEWER
        and request.method not in READ_METHODS
        and not getattr(request.scope.get("endpoint"), "viewer_allowed", False)
    ):
        raise ForbiddenException(STAFF_ONLY)

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
    message="Bu işlem yalnızca işletme sahibi ve yöneticilere açıktır.",
)

require_owner = _require_roles(
    MembershipRole.OWNER,
    message="Bu işlem yalnızca işletme sahibine açıktır.",
)


FINANCE_ONLY = "Bu işlem yalnızca işletme sahibi ve yöneticilere açıktır."


def require_finance(membership: Membership = Depends(get_business_membership)) -> Membership:
    """Money and invoice writes: same rule as reports, insights and global search."""
    from app.ai.agents.tools.common import can_view_finance

    if not can_view_finance(membership.role):
        raise ForbiddenException(FINANCE_ONLY)
    return membership


def require_staff(membership: Membership = Depends(get_business_membership)) -> Membership:
    """Day-to-day writes (selling a product or a package, marking a session): everyone but viewers."""
    if membership.role == MembershipRole.VIEWER:
        raise ForbiddenException(STAFF_ONLY)
    return membership
