from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.base_repository import BaseRepository
from app.modules.customers.models import Customer


class CustomerRepository(
    BaseRepository[Customer]
):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Customer,
        )


    def list_by_business(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Customer]:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
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


    def get_by_business(
        self,
        business_id: UUID,
        customer_id: UUID,
    ) -> Customer | None:

        statement = (
            select(self.model)
            .where(
                self.model.id == customer_id,
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)


    def get_by_phone(
        self,
        business_id: UUID,
        phone: str,
    ) -> Customer | None:
        """Matches on digits only, so '0532 111 22 33' and '05321112233' are the same customer."""

        digits = "".join(ch for ch in phone if ch.isdigit())
        if not digits:
            return None

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
                func.regexp_replace(self.model.phone, r"\D", "", "g") == digits,
            )
            .order_by(self.model.created_at)
            .limit(1)
        )

        return self.db.scalar(statement)


    def search_by_name(
        self,
        business_id: UUID,
        query: str,
    ) -> list[Customer]:

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


    def count_by_business(
        self,
        business_id: UUID,
    ) -> int:

        statement = (
            select(func.count())
            .select_from(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement) or 0

    def list_by_business_filtered(
        self,
        business_id: UUID,
        tag_ids: list[UUID] | None = None,
        status: str | None = None,
        min_visits: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        search: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[Customer]:
        from app.modules.customer_tags.models import CustomerTagAssignment
        from sqlalchemy import or_

        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )

        if search:
            statement = statement.where(
                or_(
                    self.model.name.ilike(f"%{search}%"),
                    self.model.phone.ilike(f"%{search}%"),
                    self.model.email.ilike(f"%{search}%")
                )
            )

        if tag_ids:
            for tag_id in tag_ids:
                statement = statement.where(
                    self.model.id.in_(
                        select(CustomerTagAssignment.customer_id).where(
                            CustomerTagAssignment.tag_id == tag_id,
                            CustomerTagAssignment.is_deleted.is_(False)
                        )
                    )
                )

        if status:
            statement = statement.where(self.model.status == status)

        if date_from:
            statement = statement.where(self.model.created_at >= date_from)
            
        if date_to:
            statement = statement.where(self.model.created_at <= date_to)

        statement = statement.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())
