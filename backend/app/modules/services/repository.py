from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository
from app.modules.services.models import Service
from app.shared.enums.service import ServiceStatus


class ServiceRepository(
    BaseRepository[Service]
):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Service,
        )

    def list_by_business(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 50,
    ) -> list[Service]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.name.asc(),
            )
            .offset(
                (page - 1) * size,
            )
            .limit(size)
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_by_business(
        self,
        business_id: UUID,
        service_id: UUID,
    ) -> Service | None:

        statement = (
            select(self.model)
            .where(
                self.model.id == service_id,
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    def list_active_by_business(
        self,
        business_id: UUID,
    ) -> list[Service]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.status == ServiceStatus.ACTIVE,
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.name.asc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def list_by_category(
        self,
        business_id: UUID,
        category: str,
    ) -> list[Service]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.category == category,
                self.model.is_deleted.is_(False),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def search_by_name(
        self,
        business_id: UUID,
        query: str,
    ) -> list[Service]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.name.ilike(f"%{query}%"),
                self.model.is_deleted.is_(False),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )
