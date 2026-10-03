from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional, Dict
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.modules.reminders.repository import ReminderConfigRepository, ReminderLogRepository
from app.modules.reminders.service import ReminderService
from app.modules.reminders.schemas import ReminderConfigCreate, ReminderConfigUpdate, ReminderConfigResponse, ReminderLogResponse
from app.shared.security.business import require_business_member

router = APIRouter(prefix="/businesses/{business_id}/reminders", tags=["Reminders"], dependencies=[Depends(require_business_member)])

def get_service(db: Session = Depends(get_db)) -> ReminderService:
    config_repo = ReminderConfigRepository(db)
    log_repo = ReminderLogRepository(db)
    uow = UnitOfWork(db)
    return ReminderService(config_repository=config_repo, log_repository=log_repo, uow=uow)

@router.post("/configs", response_model=ReminderConfigResponse, status_code=status.HTTP_201_CREATED)
def create_config(
    business_id: UUID, 
    data: ReminderConfigCreate, 
    service: ReminderService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    return service.create_config(business_id=business_id, data=data)

@router.get("/configs", response_model=List[ReminderConfigResponse])
def list_configs(
    business_id: UUID, 
    page: int = Query(1, ge=1), 
    size: int = Query(20, ge=1),
    service: ReminderService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    return service.list_configs(business_id=business_id, page=page, size=size)

@router.patch("/configs/{config_id}", response_model=ReminderConfigResponse)
def update_config(
    business_id: UUID, 
    config_id: UUID, 
    data: ReminderConfigUpdate,
    service: ReminderService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    return service.update_config(business_id=business_id, config_id=config_id, data=data)

@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(
    business_id: UUID, 
    config_id: UUID, 
    service: ReminderService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    service.delete_config(business_id=business_id, config_id=config_id)

@router.get("/logs", response_model=List[ReminderLogResponse])
def list_logs(
    business_id: UUID, 
    appointment_id: Optional[UUID] = None,
    page: int = Query(1, ge=1), 
    size: int = Query(20, ge=1),
    service: ReminderService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    return service.list_logs(business_id=business_id, appointment_id=appointment_id, page=page, size=size)

@router.post("/send-test/{config_id}")
def send_test_reminder(
    business_id: UUID, 
    config_id: UUID, 
    service: ReminderService = Depends(get_service), 
    current_user: User = Depends(get_current_user)
):
    return service.send_test_reminder(business_id=business_id, config_id=config_id)
