from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork

from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import (
    NotificationResponse,
)
from app.modules.notifications.service import NotificationService
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user

router = APIRouter(
    prefix="/businesses/{business_id}/notifications",
    tags=["Notifications"],
)

def get_service(db: Session = Depends(get_db)) -> NotificationService:
    repository = NotificationRepository(db)
    uow = UnitOfWork(db)
    return NotificationService(repository=repository, uow=uow)


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="List notifications",
)
def list_notifications(
    business_id: UUID,
    unread_only: bool = Query(False),
    page: int = 1,
    size: int = 20,
    service: NotificationService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    return service.list_notifications(business_id, current_user.id, unread_only, page, size)

@router.get(
    "/unread-count",
    summary="Get unread count",
)
def get_unread_count(
    business_id: UUID,
    service: NotificationService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    count = service.get_unread_count(business_id, current_user.id)
    return {"count": count}

@router.post(
    "/{notification_id}/read",
    summary="Mark as read",
)
def mark_as_read(
    business_id: UUID,
    notification_id: UUID,
    service: NotificationService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    service.mark_as_read(notification_id)
    return {"status": "success"}

@router.post(
    "/read-all",
    summary="Mark all as read",
)
def mark_all_as_read(
    business_id: UUID,
    service: NotificationService = Depends(get_service),
    current_user: User = Depends(get_current_user),
):
    service.mark_all_as_read(business_id, current_user.id)
    return {"status": "success"}
