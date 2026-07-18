from uuid import UUID

from fastapi import APIRouter, Depends

from app.modules.business.dependencies import get_business_service
from app.modules.business.schemas import (
    BusinessCreate,
    BusinessResponse,
)
from app.modules.business.service import BusinessService

router = APIRouter(
    prefix="/business",
    tags=["Business"],
)


@router.post(
    "",
    response_model=BusinessResponse,
)
def create_business(
    business: BusinessCreate,
    service: BusinessService = Depends(get_business_service),
):
    return service.create(business)


@router.get(
    "",
    response_model=list[BusinessResponse],
)
def list_businesses(
    service: BusinessService = Depends(get_business_service),
):
    return service.list()


@router.get(
    "/{business_id}",
    response_model=BusinessResponse,
)
def get_business(
    business_id: UUID,
    service: BusinessService = Depends(get_business_service),
):
    return service.get(business_id)