from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.invitation.models import Invitation
from app.shared.enums.invitation import InvitationStatus


class InvitationRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create(
        self,
        invitation: Invitation,
    ) -> Invitation:

        self.db.add(invitation)

        self.db.commit()

        self.db.refresh(invitation)

        self.db.refresh(
            invitation,
            attribute_names=[
                "business",
            ],
        )

        return invitation

    def get_by_token(
        self,
        token: str,
    ) -> Invitation | None:

        statement = (
            select(Invitation)
            .options(
                joinedload(Invitation.business),
            )
            .where(
                Invitation.token == token,
                Invitation.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    def get_pending_invitation(
        self,
        business_id,
        email: str,
    ) -> Invitation | None:

        statement = (
            select(Invitation)
            .where(
                Invitation.business_id == business_id,
                Invitation.email == email,
                Invitation.status == InvitationStatus.PENDING,
                Invitation.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    def get_business_invitations(
        self,
        business_id,
    ) -> list[Invitation]:

        statement = (
            select(Invitation)
            .options(
                joinedload(Invitation.business),
            )
            .where(
                Invitation.business_id == business_id,
                Invitation.is_deleted.is_(False),
            )
            .order_by(
                Invitation.created_at.desc(),
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def update(
        self,
        invitation: Invitation,
    ) -> Invitation:

        self.db.commit()

        self.db.refresh(invitation)

        return invitation

    def get_by_token_simple(
        self,
        token: str,
    ) -> Invitation | None:

        statement = (
            select(Invitation)
            .where(
                Invitation.token == token,
                Invitation.is_deleted.is_(False),
            )
        )

        return self.db.scalar(statement)

    def save(
        self,
        invitation: Invitation,
    ) -> Invitation:

        self.db.commit()

        self.db.refresh(invitation)

        self.db.refresh(
            invitation,
            attribute_names=[
                "business",
            ],
        )

        return invitation