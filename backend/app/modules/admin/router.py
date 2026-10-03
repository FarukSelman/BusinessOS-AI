from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.admin.schemas import (
    AdminBusinessResponse,
    AdminBusinessStatusUpdate,
    AdminBusinessPlanUpdate,
    AdminUserResponse,
)
from app.modules.admin.service import AdminService
from app.modules.business.models import Business
from app.modules.business.repository import BusinessRepository
from app.modules.user.models import User
from app.modules.user.repository import UserRepository

from app.shared.security.permissions import require_superadmin


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


# --------------------------------------------------
# Dependency
# --------------------------------------------------

def get_service(
    db: Session = Depends(get_db),
) -> AdminService:

    return AdminService(
        business_repository=BusinessRepository(db),
        user_repository=UserRepository(db),
        uow=UnitOfWork(db),
    )


def _to_business_response(business: Business) -> AdminBusinessResponse:
    return AdminBusinessResponse(
        id=business.id,
        name=business.name,
        slug=business.slug,
        industry=business.industry,
        email=business.email,
        phone=business.phone,
        status=business.status,
        plan=business.plan,
        member_count=len(business.memberships),
        created_at=business.created_at,
        updated_at=business.updated_at,
    )


# --------------------------------------------------
# Businesses
# --------------------------------------------------

@router.get(
    "/businesses",
    response_model=list[AdminBusinessResponse],
)
def list_businesses(
    page: int = 1,
    size: int = 20,
    service: AdminService = Depends(get_service),
    _: User = Depends(require_superadmin),
):
    businesses = service.list_businesses(page=page, size=size)
    return [_to_business_response(b) for b in businesses]


@router.patch(
    "/businesses/{business_id}/status",
    response_model=AdminBusinessResponse,
)
def update_business_status(
    business_id: UUID,
    data: AdminBusinessStatusUpdate,
    service: AdminService = Depends(get_service),
    _: User = Depends(require_superadmin),
):
    business = service.update_business_status(business_id, data.status)
    return _to_business_response(business)


@router.patch(
    "/businesses/{business_id}/plan",
    response_model=AdminBusinessResponse,
)
def update_business_plan(
    business_id: UUID,
    data: AdminBusinessPlanUpdate,
    service: AdminService = Depends(get_service),
    _: User = Depends(require_superadmin),
):
    business = service.update_business_plan(business_id, data.plan)
    return _to_business_response(business)


@router.delete(
    "/businesses/{business_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_business(
    business_id: UUID,
    response: Response,
    service: AdminService = Depends(get_service),
    _: User = Depends(require_superadmin),
):
    service.delete_business(business_id)
    response.status_code = status.HTTP_204_NO_CONTENT


# --------------------------------------------------
# Users
# --------------------------------------------------

@router.get(
    "/users",
    response_model=list[AdminUserResponse],
)
def list_users(
    page: int = 1,
    size: int = 20,
    service: AdminService = Depends(get_service),
    _: User = Depends(require_superadmin),
):
    return service.list_users(page=page, size=size)