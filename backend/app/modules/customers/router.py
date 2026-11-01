from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.customers.repository import CustomerRepository
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerListItem,
    CustomerResponse,
    CustomerTagBrief,
    CustomerUpdate,
)
from app.modules.customers.service import CustomerService

from app.modules.user.models import User

from app.shared.security.dependencies import get_current_user
from app.shared.security.business import require_business_member


router = APIRouter(
    prefix="/businesses/{business_id}/customers",
    tags=["Customers"],
    dependencies=[Depends(require_business_member)],
)


# --------------------------------------------------
# Dependency
# --------------------------------------------------

def get_service(
    db: Session = Depends(get_db),
) -> CustomerService:

    repository = CustomerRepository(
        db,
    )

    uow = UnitOfWork(
        db,
    )

    return CustomerService(
        repository=repository,
        uow=uow,
    )


# --------------------------------------------------
# CREATE
# --------------------------------------------------

@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create customer",
)
def create_customer(
    business_id: UUID,

    customer: CustomerCreate,

    service: CustomerService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.create(
        business_id=business_id,
        data=customer,
    )


# --------------------------------------------------
# LIST
# --------------------------------------------------

from fastapi import Query
from typing import Any

@router.get(
    "",
    response_model=list[CustomerListItem],
    summary="List customers",
)
def list_customers(
    business_id: UUID,
    response: Response,

    tag_ids: list[UUID] | None = Query(None),
    status: str | None = None,
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    # At least this many completed appointments
    min_visits: int | None = Query(None, ge=1),

    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),

    service: CustomerService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    rows, total = service.list_filtered(
        business_id=business_id,
        tag_ids=tag_ids,
        status=status,
        search=search,
        date_from=date_from,
        date_to=date_to,
        min_visits=min_visits,
        page=page,
        size=size,
    )
    response.headers["X-Total-Count"] = str(total)
    return [_list_item(row) for row in rows]


def _list_item(row: dict) -> CustomerListItem:
    return CustomerListItem(
        **CustomerResponse.model_validate(row["customer"]).model_dump(),
        tags=[CustomerTagBrief.model_validate(t) for t in row["tags"]],
        completed_visits=row["completed_visits"],
        last_visit_date=row["last_visit_date"],
    )

@router.get(
    "/{customer_id}/history",
    response_model=dict[str, Any],
    summary="Get customer history",
)
def get_customer_history(
    business_id: UUID,
    customer_id: UUID,

    service: CustomerService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.get_history(
        business_id=business_id,
        customer_id=customer_id,
    )


# --------------------------------------------------
# GET
# --------------------------------------------------

@router.get(
    "/{customer_id}",
    response_model=CustomerListItem,
    summary="Get customer",
)
def get_customer(
    business_id: UUID,
    customer_id: UUID,

    service: CustomerService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return _list_item(service.get_detail(business_id, customer_id))


# --------------------------------------------------
# UPDATE
# --------------------------------------------------

@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update customer",
)
def update_customer(
    business_id: UUID,
    customer_id: UUID,

    data: CustomerUpdate,

    service: CustomerService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
):

    return service.update(
        business_id=business_id,
        customer_id=customer_id,
        data=data,
    )


# --------------------------------------------------
# DELETE
# --------------------------------------------------

@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete customer",
)
def delete_customer(
    business_id: UUID,
    customer_id: UUID,

    service: CustomerService = Depends(
        get_service,
    ),

    current_user: User = Depends(
        get_current_user,
    ),
) -> Response:

    service.delete(
        business_id=business_id,
        customer_id=customer_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
