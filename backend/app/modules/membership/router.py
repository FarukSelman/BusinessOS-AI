from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.membership.repository import MembershipRepository
from app.modules.membership.schemas import (
    MembershipCreate,
    MembershipResponse,
)
from app.modules.membership.service import MembershipService

router = APIRouter(
    prefix="/memberships",
    tags=["Memberships"],
)


def get_service(
    db: Session = Depends(get_db),
) -> MembershipService:
    repository = MembershipRepository(db)
    return MembershipService(repository)


@router.post(
    "",
    response_model=MembershipResponse,
)
def create_membership(
    membership: MembershipCreate,
    service: MembershipService = Depends(get_service),
):
    return service.create_membership(
        membership
    )


@router.get(
    "/user/{user_id}",
    response_model=list[MembershipResponse],
)
def get_user_memberships(
    user_id: UUID,
    service: MembershipService = Depends(get_service),
):
    return service.get_user_memberships(
        user_id
    )


@router.get(
    "/business/{business_id}",
    response_model=list[MembershipResponse],
)
def get_business_memberships(
    business_id: UUID,
    service: MembershipService = Depends(get_service),
):
    return service.get_business_memberships(
        business_id
    )