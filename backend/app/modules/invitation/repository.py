from datetime import UTC, datetime
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
    # GET BY TOKEN
    # --------------------------------------------------

    def get_by_token(
        self,
        token: str,
    ) -> Invitation | None:

        statement = (
            select(self.model)
            .options(
                joinedload(self.model.business),
            )
            .where(
                self.model.token == token,
                self.model.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    # --------------------------------------------------
    # GET PENDING INVITATION
    # --------------------------------------------------

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

    # --------------------------------------------------
    # EXISTS PENDING
    # --------------------------------------------------

    def exists_pending(
        self,
        business_id: UUID,
        email: str,
    ) -> bool:

        return (
            self.get_pending_invitation(
                business_id,
                email,
            )
            is not None
        )

    # --------------------------------------------------
    # LIST BUSINESS INVITATIONS
    # --------------------------------------------------

    def get_business_invitations(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Invitation]:

        statement = (
            select(self.model)
            .options(
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
    # LIST ACTIVE INVITATIONS BY EMAIL
    # --------------------------------------------------

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

    # --------------------------------------------------
    # IS PENDING
    # --------------------------------------------------

    def is_pending(
        self,
        invitation: Invitation,
    ) -> bool:

        return invitation.status == InvitationStatus.PENDING

    # --------------------------------------------------
    # MARK ACCEPTED
    # --------------------------------------------------

    def mark_accepted(
        self,
        invitation: Invitation,
    ) -> None:

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now(UTC)

        self.save(invitation)

    # --------------------------------------------------
    # MARK EXPIRED
    # --------------------------------------------------

    def mark_expired(
        self,
        invitation: Invitation,
    ) -> None:

        invitation.status = InvitationStatus.EXPIRED

        self.save(invitation)

    # --------------------------------------------------
    # CANCEL INVITATION
    # --------------------------------------------------

    def cancel(
        self,
        invitation: Invitation,
    ) -> None:

        invitation.is_deleted = True

        self.save(invitation)

    # --------------------------------------------------
    # GET EXPIRED INVITATIONS
    # --------------------------------------------------

    def get_expired(
        self,
    ) -> list[Invitation]:

        statement = (
            select(self.model)
            .where(
                self.model.status == InvitationStatus.PENDING,
                self.model.expires_at < datetime.now(UTC),
                self.model.is_deleted.is_(False),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    # --------------------------------------------------
    # DELETE EXPIRED INVITATIONS
    # --------------------------------------------------

    def delete_expired(
        self,
    ) -> int:

        invitations = self.get_expired()

        for invitation in invitations:
            invitation.is_deleted = True

        return len(invitations)