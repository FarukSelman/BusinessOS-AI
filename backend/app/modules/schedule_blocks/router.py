from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
from typing import List, Any
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.modules.schedule_blocks.repository import ScheduleBlockRepository
from app.modules.schedule_blocks.service import ScheduleBlockService
from app.modules.schedule_blocks.schemas import ScheduleBlockCreate, ScheduleBlockUpdate, ScheduleBlockResponse

router = APIRouter(prefix="/businesses/{business_id}/schedule-blocks", tags=["ScheduleBlocks"])

def get_service(db: Session = Depends(get_db)) -> ScheduleBlockService:
    repository = ScheduleBlockRepository(db)
    uow = UnitOfWork(db)
    return ScheduleBlockService(repository=repository, uow=uow)

@router.post("", response_model=ScheduleBlockResponse, status_code=status.HTTP_201_CREATED)
def create(
    business_id: UUID, 
    data: ScheduleBlockCreate, 
    service: ScheduleBlockService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    return service.create(business_id=business_id, data=data)

@router.get("", response_model=List[ScheduleBlockResponse])
def list_blocks(
    business_id: UUID, 
    page: int = Query(1, ge=1), 
    size: int = Query(20, ge=1),
    service: ScheduleBlockService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    return service.list(business_id=business_id, page=page, size=size)

@router.get("/for-date")
def get_blocked_times(
    business_id: UUID, 
    target_date: date = Query(..., alias="date"),
    service: ScheduleBlockService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
) -> Any:
    blocked_times = service.get_blocked_times_for_date(business_id, target_date)
    return [{"start_time": st.isoformat(), "end_time": et.isoformat()} for st, et in blocked_times]

@router.get("/{block_id}", response_model=ScheduleBlockResponse)
def get_block(
    business_id: UUID, 
    block_id: UUID, 
    service: ScheduleBlockService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    return service.get(business_id=business_id, block_id=block_id)

@router.patch("/{block_id}", response_model=ScheduleBlockResponse)
def update_block(
    business_id: UUID, 
    block_id: UUID, 
    data: ScheduleBlockUpdate,
    service: ScheduleBlockService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    return service.update(business_id=business_id, block_id=block_id, data=data)

@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(
    business_id: UUID, 
    block_id: UUID, 
    service: ScheduleBlockService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    service.delete(business_id=business_id, block_id=block_id)
