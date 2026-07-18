from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.business.models import Business


class BusinessRepository:

    def __init__(self, db: Session):
        self.db = db

    # ----------------------------
    # Create
    # ----------------------------

    def create(self, business: Business) -> Business:

        self.db.add(business)
        self.db.commit()
        self.db.refresh(business)

        return business

    # ----------------------------
    # Read
    # ----------------------------

    def get_by_id(
        self,
        business_id: UUID,
    ) -> Business | None:

        statement = select(Business).where(
            Business.id == business_id,
            Business.is_deleted == False,
        )

        return self.db.scalar(statement)

    def get(
        self,
        business_id: UUID,
    ) -> Business | None:

        return self.get_by_id(business_id)

    def get_all(self) -> list[Business]:

        statement = select(Business).where(
            Business.is_deleted == False
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_by_email(
        self,
        email: str,
    ) -> Business | None:

        statement = select(Business).where(
            Business.email == email,
            Business.is_deleted == False,
        )

        return self.db.scalar(statement)

    def get_by_slug(
        self,
        slug: str,
    ) -> Business | None:

        statement = select(Business).where(
            Business.slug == slug,
            Business.is_deleted == False,
        )

        return self.db.scalar(statement)

    # ----------------------------
    # Update
    # ----------------------------

    def update(
        self,
        business: Business,
    ) -> Business:

        self.db.commit()
        self.db.refresh(business)

        return business

    # ----------------------------
    # Delete (Soft Delete)
    # ----------------------------

    def delete(
        self,
        business: Business,
    ) -> None:

        business.is_deleted = True

        self.db.commit()