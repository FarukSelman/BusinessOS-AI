from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.services.repository import ServiceRepository
from app.modules.services.schemas import (
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)
from app.modules.services.service import ServiceService

from app.modules.user.models import User

from app.shared.security.dependencies import get_current_user


router = APIRouter(
    prefix="/businesses/{business_id}/services",
    tags=["Services"],
)


# --------------------------------------------------
# Dependency
# --------------------------------------------------

def get_service(
    db: Session = Depends(get_db),
) -> ServiceService:

    repository = ServiceRepository(
        db,
    )

    uow = UnitOfWork(
        db,
    )

    return ServiceService(
        repository=repository,
        uow=uow,
    )


# --------------------------------------------------
# CREATE
# --------------------------------------------------

@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create service",
)
def create_service(
    business_id: UUID,

    data: ServiceCreate,

    service: ServiceService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.create(
        business_id,
        data=data,
    )


# --------------------------------------------------
# LIST
# --------------------------------------------------

@router.get(
    "",
    response_model=list[ServiceResponse],
    summary="List services",
)
def list_services(
    business_id: UUID,

    page: int = 1,
    size: int = 50,

    service: ServiceService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.list(
        business_id,
        page=page,
        size=size,
    )


# --------------------------------------------------
# GET
# --------------------------------------------------

@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Get service",
)
def get_service_detail(
    business_id: UUID,
    service_id: UUID,

    service: ServiceService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.get(
        business_id,
        service_id,
    )


# --------------------------------------------------
# UPDATE
# --------------------------------------------------

@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    summary="Update service",
)
def update_service(
    business_id: UUID,
    service_id: UUID,

    data: ServiceUpdate,

    service: ServiceService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.update(
        business_id,
        service_id,
        data=data,
    )


# --------------------------------------------------
# DELETE
# --------------------------------------------------

@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete service",
)
def delete_service(
    business_id: UUID,
    service_id: UUID,

    service: ServiceService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
) -> Response:

    service.delete(
        business_id,
        service_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
