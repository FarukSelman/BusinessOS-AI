from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.business.repository import BusinessRepository
from app.modules.business.schemas import (
    BusinessCreate,
    BusinessResponse,
    BusinessUpdate,
)
from app.modules.business.service import BusinessService

from app.modules.user.models import User

from app.shared.security.permissions import require_permission
from app.shared.auth.permissions import Permission
from app.shared.security.dependencies import get_current_user
from app.shared.security.business import get_business_membership
from app.modules.membership.models import Membership
from app.ai.agents.tools.common import can_view_finance
from pydantic import BaseModel

from app.modules.membership.repository import MembershipRepository


router = APIRouter(
    prefix="/businesses",
    tags=["Businesses"],
)


# --------------------------------------------------
# Dependency
# --------------------------------------------------

def get_service(
    db: Session = Depends(get_db),
) -> BusinessService:

    repository = BusinessRepository(
        db,
    )

    membership_repository = MembershipRepository(
        db,
    )

    uow = UnitOfWork(
        db,
    )

    return BusinessService(
        repository=repository,
        membership_repository=membership_repository,
        uow=uow,
    )


# --------------------------------------------------
# CREATE
# --------------------------------------------------

@router.post(
    "",
    response_model=BusinessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create business",
)
def create_business(
    business: BusinessCreate,

    service: BusinessService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.create(
        business,
        user_id=current_user.id,
    )


# --------------------------------------------------
# LIST
# --------------------------------------------------

@router.get(
    "",
    response_model=list[BusinessResponse],
    summary="List businesses",
)
def list_businesses(
    page: int = 1,
    size: int = 20,
    service: BusinessService = Depends(get_service),
    current_user: User = Depends(get_current_user),   # require_permission değil, sadece get_current_user
):
    return service.list_for_user(
        user_id=current_user.id,
        page=page,
        size=size,
    )


# --------------------------------------------------
# GET
# --------------------------------------------------

@router.get(
    "/{business_id}",
    response_model=BusinessResponse,
    summary="Get business",
)
def get_business(
    business_id: UUID,

    service: BusinessService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.BUSINESS_READ,
        ),
    ),
):

    return service.get(
        business_id,
    )


# --------------------------------------------------
# UPDATE
# --------------------------------------------------

@router.patch(
    "/{business_id}",
    response_model=BusinessResponse,
    summary="Update business",
)
def update_business(
    business_id: UUID,

    data: BusinessUpdate,

    service: BusinessService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.BUSINESS_UPDATE,
        ),
    ),
):

    return service.update(
        business_id,
        data,
    )


# --------------------------------------------------
# DELETE
# --------------------------------------------------

@router.delete(
    "/{business_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete business",
)
def delete_business(
    business_id: UUID,

    service: BusinessService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        require_permission(
            Permission.BUSINESS_DELETE,
        ),
    ),
) -> Response:

    service.delete(
        business_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


class MyBusinessAccess(BaseModel):
    role: str
    can_view_finance: bool


@router.get(
    "/{business_id}/me",
    response_model=MyBusinessAccess,
    summary="My role in this business",
)
def get_my_access(
    business_id: UUID,
    membership: Membership = Depends(get_business_membership),
):
    """What the panel needs to show or hide finance UI (amounts, invoice actions)."""
    role = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
    return MyBusinessAccess(role=role, can_view_finance=can_view_finance(membership.role))
