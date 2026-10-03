from uuid import UUID

from app.core.exceptions import NotFoundException
from app.db.unit_of_work import UnitOfWork
from app.modules.notifications.models import Notification
from app.modules.notifications.repository import NotificationRepository
from app.shared.enums.notification import NotificationType

class NotificationService:
    def __init__(self, repository: NotificationRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    def create_notification(
        self,
        business_id: UUID,
        user_id: UUID | None,
        title: str,
        message: str,
        type: NotificationType,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
    ) -> Notification:
        notification = Notification(
            business_id=business_id,
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            reference_id=reference_id,
            reference_type=reference_type,
            is_read=False,
        )

        with self.uow:
            self.repository.create(notification)
            self.uow.flush()
            self.uow.refresh(notification)

        return notification

    def list_notifications(
        self, business_id: UUID, user_id: UUID, unread_only: bool = False, page: int = 1, size: int = 20
    ) -> list[Notification]:
        return self.repository.get_user_notifications(
            business_id, user_id, unread_only, page, size
        )

    def get_unread_count(self, business_id: UUID, user_id: UUID) -> int:
        return self.repository.get_unread_count(business_id, user_id)

    def mark_as_read(self, business_id: UUID, notification_id: UUID, user_id: UUID) -> None:
        notification = self.repository.get(notification_id)
        # Only the business's own notifications, and only those addressed to
        # this user (or broadcast to the whole business), can be marked.
        if (
            not notification
            or notification.business_id != business_id
            or (notification.user_id is not None and notification.user_id != user_id)
        ):
            raise NotFoundException("Notification not found.")
        
        with self.uow:
            self.repository.mark_as_read(notification_id)
            self.uow.flush()

    def mark_all_as_read(self, business_id: UUID, user_id: UUID) -> None:
        with self.uow:
            self.repository.mark_all_as_read(business_id, user_id)
            self.uow.flush()
