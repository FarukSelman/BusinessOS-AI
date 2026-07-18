from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.exceptions import BadRequestException
from app.modules.invitation.models import Invitation
from app.modules.invitation.repository import InvitationRepository
from app.modules.invitation.schemas import InvitationCreate
from app.modules.membership.models import Membership
from app.modules.membership.repository import MembershipRepository
from app.shared.enums.invitation import InvitationStatus
from app.shared.mail.service import MailService


class InvitationService:

    def __init__(
        self,
        repository: InvitationRepository,
        membership_repository: MembershipRepository,
    ):
        self.repository = repository
        self.membership_repository = membership_repository

    def create_invitation(
        self,
        data: InvitationCreate,
    ) -> Invitation:

        existing = self.repository.get_pending_invitation(
            data.business_id,
            data.email,
        )

        if existing:
            raise BadRequestException(
                "A pending invitation already exists for this email."
            )

        invitation = Invitation(
            business_id=data.business_id,
            email=data.email,
            role=data.role,
            token=str(uuid4()),
            status=InvitationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )

        created_invitation = self.repository.create(
            invitation
        )

        invitation_link = (
            f"http://localhost:8000/api/v1/invitations/accept/"
            f"{created_invitation.token}"
        )

        try:
            MailService.send_invitation(
                email=created_invitation.email,
                business_name=created_invitation.business.name,
                invitation_link=invitation_link,
            )
        except Exception as e:
            print(f"Mail gönderilemedi: {e}")

        return created_invitation

    def get_business_invitations(
        self,
        business_id,
    ):
        return self.repository.get_business_invitations(
            business_id
        )

    def get_invitation_by_token(
        self,
        token: str,
    ) -> Invitation:

        invitation = self.repository.get_by_token(
            token
        )

        if invitation is None:
            raise BadRequestException(
                "Invitation not found."
            )

        return invitation

    def accept_invitation(
        self,
        token: str,
        user_id,
    ):

        invitation = self.repository.get_by_token(
            token
        )

        if invitation is None:
            raise BadRequestException(
                "Invitation not found."
            )

        if invitation.status != InvitationStatus.PENDING:
            raise BadRequestException(
                "Invitation already used."
            )

        if invitation.expires_at.replace(
            tzinfo=UTC
        ) < datetime.now(UTC):
            raise BadRequestException(
                "Invitation expired."
            )

        existing = (
            self.membership_repository
            .get_by_user_and_business(
                user_id,
                invitation.business_id,
            )
        )

        if existing:
            raise BadRequestException(
                "User is already a member."
            )

        membership = Membership(
            user_id=user_id,
            business_id=invitation.business_id,
            role=invitation.role,
        )

        self.membership_repository.create(
            membership
        )

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.now(UTC)

        return self.repository.save(
            invitation
        )