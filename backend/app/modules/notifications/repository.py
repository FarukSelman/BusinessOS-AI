from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository
from app.modules.notifications.models import Notification

class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Notification)

    def get_user_notifications(
        self, business_id: UUID, user_id: UUID, unread_only: bool = False, page: int = 1, size: int = 20
    ) -> list[Notification]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
            # user_id is either the user or None (broadcast)
            (self.model.user_id == user_id) | (self.model.user_id.is_(None))
        )

        if unread_only:
            query = query.where(self.model.is_read.is_(False))

        query = query.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())

    def get_unread_count(self, business_id: UUID, user_id: UUID) -> int:
        statement = select(func.count(self.model.id)).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
            (self.model.user_id == user_id) | (self.model.user_id.is_(None)),
            self.model.is_read.is_(False)
        )
        return self.db.scalar(statement) or 0

    def mark_as_read(self, notification_id: UUID) -> None:
        statement = update(self.model).where(self.model.id == notification_id).values(is_read=True)
        self.db.execute(statement)

    def mark_all_as_read(self, business_id: UUID, user_id: UUID) -> None:
        statement = update(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
            (self.model.user_id == user_id) | (self.model.user_id.is_(None)),
            self.model.is_read.is_(False)
        ).values(is_read=True)
        self.db.execute(statement)
