from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.branches.repository import BranchRepository
from app.modules.business_hours.repository import BusinessHoursRepository
from app.modules.business_hours.schemas import (
    BusinessHoursResponse,
    BusinessHoursSet,
    OpenWindowResponse,
)
from app.modules.business_hours.service import BusinessHoursService
from app.modules.user.models import User
from app.shared.auth.permissions import Permission
from app.shared.security.business import require_member
from app.shared.security.permissions import require_permission

# Reading: any member. Changing: roles with BUSINESS_UPDATE (OWNER, ADMIN).
require_hours_editor = require_permission(Permission.BUSINESS_UPDATE)

router = APIRouter(prefix="/businesses/{business_id}/business-hours", tags=["BusinessHours"])


def get_service(db: Session = Depends(get_db)) -> BusinessHoursService:
    return BusinessHoursService(
        repository=BusinessHoursRepository(db),
        uow=UnitOfWork(db),
        branch_repo=BranchRepository(db),
    )


@router.get("", response_model=List[BusinessHoursResponse])
def get_hours(
    business_id: UUID,
    branch_id: Optional[UUID] = Query(None, description="Omit for business-wide hours"),
    service: BusinessHoursService = Depends(get_service),
    current_user: User = Depends(require_member),
):
    return service.get_hours(business_id=business_id, branch_id=branch_id)


@router.put("", response_model=List[BusinessHoursResponse])
def set_hours(
    business_id: UUID,
    data: BusinessHoursSet,
    branch_id: Optional[UUID] = Query(None, description="Omit for business-wide hours"),
    service: BusinessHoursService = Depends(get_service),
    current_user: User = Depends(require_hours_editor),
):
    return service.set_hours(business_id=business_id, data=data, branch_id=branch_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def reset_branch_hours(
    business_id: UUID,
    branch_id: UUID = Query(..., description="Branch whose own hours are removed (falls back to business hours)"),
    service: BusinessHoursService = Depends(get_service),
    current_user: User = Depends(require_hours_editor),
):
    service.reset_branch_hours(business_id=business_id, branch_id=branch_id)


@router.get("/open-window", response_model=OpenWindowResponse)
def get_open_window(
    business_id: UUID,
    target_date: date = Query(..., alias="date"),
    branch_id: Optional[UUID] = Query(None),
    service: BusinessHoursService = Depends(get_service),
    current_user: User = Depends(require_member),
):
    window = service.get_open_window(business_id, target_date, branch_id)
    return OpenWindowResponse(
        date=target_date,
        branch_id=branch_id,
        is_open=window is not None,
        open_time=window[0] if window else None,
        close_time=window[1] if window else None,
    )
