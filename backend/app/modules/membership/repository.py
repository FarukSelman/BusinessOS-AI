from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.base_repository import BaseRepository
from app.modules.membership.models import Membership
from app.shared.enums.membership import MembershipRole
from fastapi import HTTPException, status


class MembershipRepository(BaseRepository[Membership]):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Membership,
        )

    # --------------------------------------------------
    # GET USER + BUSINESS MEMBERSHIP
    # --------------------------------------------------

    def get_by_user_and_business(
        self,
        user_id: UUID,
        business_id: UUID,
    ) -> Membership | None:

        statement = (
            select(self.model)
            .options(
                joinedload(self.model.user),
                joinedload(self.model.business),
            )
            .where(
                self.model.user_id == user_id,
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)
    
        # --------------------------------------------------
    # GET MEMBERSHIP BY BUSINESS + ID
    # --------------------------------------------------

    def get_by_business_and_id(
        self,
        business_id: UUID,
        membership_id: UUID,
    ) -> Membership | None:

        statement = (
            select(self.model)
            .options(
                joinedload(self.model.user),
                joinedload(self.model.business),
            )
            .where(
                self.model.id == membership_id,
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    # --------------------------------------------------
    # CHECK EXISTENCE
    # --------------------------------------------------

    def exists_by_user_and_business(
        self,
        user_id: UUID,
        business_id: UUID,
    ) -> bool:

        return (
            self.get_by_user_and_business(
                user_id,
                business_id,
            )
            is not None
        )

    # --------------------------------------------------
    # OWNER CHECK
    # --------------------------------------------------

    def is_owner(
        self,
        user_id: UUID,
        business_id: UUID,
    ) -> bool:

        statement = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.business_id == business_id,
                self.model.role == MembershipRole.OWNER,
                self.model.is_deleted.is_(False),
            )
        )

        membership = self.db.scalar(
            statement,
        )

        return membership is not None

    # --------------------------------------------------
    # ROLE CHECK
    # --------------------------------------------------

    def has_role(
        self,
        user_id: UUID,
        business_id: UUID,
        role: MembershipRole,
    ) -> bool:

        statement = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.business_id == business_id,
                self.model.role == role,
                self.model.is_deleted.is_(False),
            )
        )

        membership = self.db.scalar(
            statement,
        )

        return membership is not None

    # --------------------------------------------------
    # USER MEMBERSHIPS
    # --------------------------------------------------

    def get_user_memberships(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Membership]:

        statement = (
            select(self.model)
            .options(
                joinedload(self.model.user),
                joinedload(self.model.business),
            )
            .where(
                self.model.user_id == user_id,
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.created_at.desc(),
            )
            .offset(
                (page - 1) * size,
            )
            .limit(size)
        )

        return list(
            self.db.scalars(statement).all()
        )

    # --------------------------------------------------
    # BUSINESS MEMBERSHIPS
    # --------------------------------------------------

    def get_business_memberships(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Membership]:

        statement = (
            select(self.model)
            .options(
                joinedload(self.model.user),
                joinedload(self.model.business),
            )
            .where(
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.created_at.desc(),
            )
            .offset(
                (page - 1) * size,
            )
            .limit(size)
        )

        return list(
            self.db.scalars(statement).all()
        )
    
    # --------------------------------------------------
    # Permission helper
    # --------------------------------------------------

    def require_membership(
        self,
        user_id: UUID,
        business_id: UUID,
    ) -> Membership:

        membership = self.get_by_user_and_business(
            user_id=user_id,
            business_id=business_id,
        )

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of this business.",
            )

        return membership
    
        # --------------------------------------------------
    # UPDATE MEMBERSHIP ROLE
    # --------------------------------------------------

    def update_role(
        self,
        membership_id: UUID,
        role: MembershipRole,
    ) -> Membership | None:

        statement = (
            select(self.model)
            .options(
                joinedload(self.model.user),
                joinedload(self.model.business),
            )
            .where(
                self.model.id == membership_id,
                self.model.is_deleted.is_(False),
            )
        )

        membership = self.db.scalar(
            statement,
        )

        if membership is None:
            return None

        membership.role = role

        self.db.flush()

        return membership
    
        # --------------------------------------------------
    # COUNT OWNERS
    # --------------------------------------------------

    def count_owners(
        self,
        business_id: UUID,
    ) -> int:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.role == MembershipRole.OWNER,
                self.model.is_deleted.is_(False),
            )
        )

        return len(
            self.db.scalars(statement).all()
        )