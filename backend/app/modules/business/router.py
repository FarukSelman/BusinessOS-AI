from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.modules.business.repository import BusinessRepository
from app.modules.business.schemas import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse,
)
from app.modules.business.service import BusinessService

from app.modules.user.models import User

from app.shared.security.dependencies import (
    get_current_user,
)

from app.shared.security.business import (
    require_owner,
)

router = APIRouter(
    prefix="/business",
    tags=["Business"],
)


def get_service(
    db: Session = Depends(get_db),
):
    repository = BusinessRepository(db)
    return BusinessService(repository)


@router.post(
    "",
    response_model=BusinessResponse,
)
def create_business(
    business: BusinessCreate,
    service: BusinessService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    return service.create(business)


@router.get(
    "",
    response_model=list[BusinessResponse],
)
def list_businesses(
    service: BusinessService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    return service.list()


@router.get(
    "/{business_id}",
    response_model=BusinessResponse,
)
def get_business(
    business_id: UUID,
    service: BusinessService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    return service.get(business_id)


@router.put(
    "/{business_id}",
    response_model=BusinessResponse,
)
def update_business(
    business_id: UUID,
    data: BusinessUpdate,
    service: BusinessService = Depends(get_service),
    current_user: User = Depends(require_owner),
):
    return service.update(
        business_id,
        data,
    )


@router.delete(
    "/{business_id}",
    status_code=204,
)
def delete_business(
    business_id: UUID,
    service: BusinessService = Depends(get_service),
    current_user: User = Depends(require_owner),
):
    service.delete(business_id)