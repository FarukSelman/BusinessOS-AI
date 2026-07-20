from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.base_repository import BaseRepository
from app.modules.invitation.models import Invitation
from app.shared.enums.invitation import InvitationStatus


class InvitationRepository(BaseRepository[Invitation]):

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=Invitation,
        )

    # --------------------------------------------------
    # Queries
    # --------------------------------------------------

    def get_by_token(
        self,
        token: str,
    ) -> Invitation | None:

        statement = (
            select(self.model)
            .options(
                joinedload(
                    self.model.business,
                ),
            )
            .where(
                self.model.token == token,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    def get_pending_invitation(
        self,
        business_id: UUID,
        email: str,
    ) -> Invitation | None:

        statement = (
            select(self.model)
            .where(
                self.model.business_id == business_id,
                self.model.email == email,
                self.model.status == InvitationStatus.PENDING,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    def exists_pending(
        self,
        business_id: UUID,
        email: str,
    ) -> bool:

        return (
            self.get_pending_invitation(
                business_id=business_id,
                email=email,
            )
            is not None
        )

    def get_business_invitations(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Invitation]:

        statement = (
            select(self.model)
            .options(
                joinedload(
                    self.model.business,
                ),
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

    def get_active_by_email(
        self,
        email: str,
    ) -> list[Invitation]:

        statement = (
            select(self.model)
            .where(
                self.model.email == email,
                self.model.status == InvitationStatus.PENDING,
                self.model.is_deleted.is_(False),
            )
            .order_by(
                self.model.created_at.desc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )