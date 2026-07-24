from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.membership.repository import MembershipRepository
from app.modules.membership.schemas import (
    MembershipCreate,
    MembershipUpdate,
    MembershipResponse,
)
from app.modules.membership.service import MembershipService

from app.modules.user.models import User

from app.shared.security.permissions import require_permission
from app.shared.auth.permissions import Permission


router = APIRouter(
    prefix="/businesses/{business_id}/memberships",
    tags=["Memberships"],
)


# ---------------------------------------------------------
# Dependency
# ---------------------------------------------------------

def get_service(
    db: Session = Depends(get_db),
) -> MembershipService:

    repository = MembershipRepository(
        db,
    )

    uow = UnitOfWork(
        db,
    )

    return MembershipService(
        repository=repository,
        uow=uow,
    )


# ---------------------------------------------------------
# CREATE MEMBERSHIP
# ---------------------------------------------------------

@router.post(
    "",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create membership",
)
def create_membership(
    business_id: UUID,

    membership: MembershipCreate,

    service: MembershipService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.MEMBERSHIP_CREATE,
        ),
    ),
):

    return service.create_membership(
        business_id=business_id,
        data=membership,
    )


# ---------------------------------------------------------
# LIST BUSINESS MEMBERS
# ---------------------------------------------------------

@router.get(
    "",
    response_model=list[MembershipResponse],
    summary="List business memberships",
)
def get_business_memberships(
    business_id: UUID,

    page: int = 1,
    size: int = 20,

    service: MembershipService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.MEMBERSHIP_READ,
        ),
    ),
):

    return service.get_business_memberships(
        business_id=business_id,
        page=page,
        size=size,
    )


# ---------------------------------------------------------
# LIST USER MEMBERSHIPS
# ---------------------------------------------------------

@router.get(
    "/user/{user_id}",
    response_model=list[MembershipResponse],
    summary="List user memberships",
)
def get_user_memberships(
    business_id: UUID,

    user_id: UUID,

    page: int = 1,
    size: int = 20,

    service: MembershipService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.MEMBERSHIP_READ,
        ),
    ),
):

    return service.get_user_memberships(
        user_id=user_id,
        page=page,
        size=size,
    )


# ---------------------------------------------------------
# UPDATE MEMBERSHIP ROLE
# ---------------------------------------------------------

@router.patch(
    "/{membership_id}",
    response_model=MembershipResponse,
    summary="Update membership role",
)
def update_membership(
    business_id: UUID,

    membership_id: UUID,

    data: MembershipUpdate,

    service: MembershipService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.MEMBERSHIP_UPDATE,
        ),
    ),
):

    return service.update_membership(
        business_id=business_id,
        membership_id=membership_id,
        data=data,
    )


# ---------------------------------------------------------
# DELETE MEMBERSHIP
# ---------------------------------------------------------

@router.delete(
    "/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete membership",
)
def delete_membership(
    business_id: UUID,

    membership_id: UUID,

    service: MembershipService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.MEMBERSHIP_DELETE,
        ),
    ),
):

    service.delete(
        business_id=business_id,
        membership_id=membership_id,
    )