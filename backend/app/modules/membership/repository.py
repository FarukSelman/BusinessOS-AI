from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.membership.models import Membership
from app.shared.enums.membership import MembershipRole


class MembershipRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create(
        self,
        membership: Membership,
    ) -> Membership:

        self.db.add(membership)

        self.db.commit()

        self.db.refresh(membership)

        self.db.refresh(
            membership,
            attribute_names=[
                "user",
                "business",
            ],
        )

        return membership

    def get_by_user_and_business(
        self,
        user_id,
        business_id,
    ) -> Membership | None:

        statement = (
            select(Membership)
            .options(
                joinedload(Membership.user),
                joinedload(Membership.business),
            )
            .where(
                Membership.user_id == user_id,
                Membership.business_id == business_id,
                Membership.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    def get_user_memberships(
        self,
        user_id,
    ) -> list[Membership]:

        statement = (
            select(Membership)
            .options(
                joinedload(Membership.user),
                joinedload(Membership.business),
            )
            .where(
                Membership.user_id == user_id,
                Membership.is_deleted.is_(False),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_business_memberships(
        self,
        business_id,
    ) -> list[Membership]:

        statement = (
            select(Membership)
            .options(
                joinedload(Membership.user),
                joinedload(Membership.business),
            )
            .where(
                Membership.business_id == business_id,
                Membership.is_deleted.is_(False),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_by_id(
        self,
        membership_id,
    ) -> Membership | None:

        statement = (
            select(Membership)
            .options(
                joinedload(Membership.user),
                joinedload(Membership.business),
            )
            .where(
                Membership.id == membership_id,
                Membership.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    def delete(
        self,
        membership: Membership,
    ) -> Membership:

        membership.is_deleted = True

        self.db.commit()

        self.db.refresh(membership)

        return membership

    def is_owner(
        self,
        user_id,
        business_id,
    ) -> bool:

        membership = self.get_by_user_and_business(
            user_id,
            business_id,
        )

        if membership is None:
            return False

        return membership.role == MembershipRole.OWNER

    def is_admin(
        self,
        user_id,
        business_id,
    ) -> bool:

        membership = self.get_by_user_and_business(
            user_id,
            business_id,
        )

        if membership is None:
            return False

        return membership.role in (
            MembershipRole.OWNER,
            MembershipRole.ADMIN,
        )