from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository
from app.modules.business.models import Business


class BusinessRepository(
    BaseRepository[Business]
):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Business,
        )


    def get_by_slug(
        self,
        slug: str,
    ) -> Business | None:

        statement = (
            select(self.model)
            .where(
                self.model.slug == slug,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)


    def exists_by_slug(
        self,
        slug: str,
    ) -> bool:

        # The unique index covers soft-deleted rows too, so check all of them.
        statement = select(self.model.id).where(
            self.model.slug == slug,
        )

        return self.db.scalar(statement) is not None


    def list_paginated(
        self,
        page: int = 1,
        size: int = 20,
    ) -> list[Business]:

        statement = (
            select(self.model)
            .where(
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.created_at.desc(),
            )
            .offset(
                (page - 1) * size
            )
            .limit(size)
        )

        return list(
            self.db.scalars(statement).all()
        )
    
    def exists_by_email(
        self,
        email: str,
    ) -> bool:

        statement = (
            select(self.model)
            .where(
                self.model.email == email,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement) is not None