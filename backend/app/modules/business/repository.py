from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.business.models import Business


class BusinessRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Business | None:

        statement = select(Business).where(
            Business.email == email
        )

        return self.db.scalar(statement)

    def get_by_slug(self, slug: str) -> Business | None:

        statement = select(Business).where(
            Business.slug == slug
        )

        return self.db.scalar(statement)

    def create(
        self,
        business: Business,
    ) -> Business:

        self.db.add(business)
        self.db.commit()
        self.db.refresh(business)

        return business