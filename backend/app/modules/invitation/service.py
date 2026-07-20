from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
import logging

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    BadRequestException,
)

from app.db.unit_of_work import UnitOfWork

from app.modules.invitation.models import Invitation
from app.modules.invitation.repository import InvitationRepository
from app.modules.invitation.schemas import InvitationCreate

from app.modules.membership.models import Membership
from app.modules.membership.repository import MembershipRepository

from app.shared.enums.invitation import InvitationStatus
from app.shared.mail.service import MailService


logger = logging.getLogger(__name__)


class InvitationService:


    def __init__(
        self,
        repository: InvitationRepository,
        membership_repository: MembershipRepository,
        uow: UnitOfWork,
    ):

        self.repository = repository
        self.membership_repository = membership_repository
        self.uow = uow



    # --------------------------------------------------
    # CREATE INVITATION
    # --------------------------------------------------

    def create_invitation(
        self,
        business_id: UUID,
        data: InvitationCreate,
    ) -> Invitation:


        if self.repository.exists_pending(
            business_id,
            data.email,
        ):

            raise ConflictException(
                "A pending invitation already exists for this email.",
            )


        invitation = Invitation(
            business_id=business_id,
            email=data.email,
            role=data.role,
            token=str(uuid4()),
            status=InvitationStatus.PENDING,
            expires_at=datetime.now(UTC)
            + timedelta(days=7),
        )


        with self.uow:

            self.repository.create(
                invitation,
            )

            self.uow.flush()

            self.uow.refresh(
                invitation,
                relationships=[
                    "business",
                ],
            )


        invitation_link = (
            "http://localhost:8000/api/v1/"
            f"invitations/accept/{invitation.token}"
        )


        try:

            MailService.send_invitation(
                email=invitation.email,
                business_name=invitation.business.name,
                invitation_link=invitation_link,
            )


        except Exception as exc:

            logger.error(
                "Invitation email failed: %s",
                exc,
            )


        return invitation



    # --------------------------------------------------
    # LIST
    # --------------------------------------------------

    def get_business_invitations(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Invitation]:


        return self.repository.get_business_invitations(
            business_id=business_id,
            page=page,
            size=size,
        )



    # --------------------------------------------------
    # GET BY TOKEN
    # --------------------------------------------------

    def get_invitation_by_token(
        self,
        token: str,
    ) -> Invitation:


        invitation = self.repository.get_by_token(
            token,
        )


        if invitation is None:

            raise NotFoundException(
                "Invitation not found.",
            )


        return invitation



    # --------------------------------------------------
    # ACCEPT INVITATION
    # --------------------------------------------------

    def accept_invitation(
        self,
        token: str,
        user_id: UUID,
    ) -> Invitation:


        invitation = self.get_invitation_by_token(
            token,
        )


        if not self.repository.is_pending(invitation):

            raise BadRequestException(
                "Invitation already used.",
            )


        expires_at = invitation.expires_at


        if expires_at.tzinfo is None:

            expires_at = expires_at.replace(
                tzinfo=UTC,
            )


        if expires_at < datetime.now(UTC):

            raise BadRequestException(
                "Invitation expired.",
            )


        if self.membership_repository.exists_by_user_and_business(
            user_id,
            invitation.business_id,
        ):

            raise ConflictException(
                "User is already a member.",
            )


        membership = Membership(
            user_id=user_id,
            business_id=invitation.business_id,
            role=invitation.role,
        )


        with self.uow:

            self.membership_repository.create(
                membership,
            )


            self.repository.mark_accepted(invitation)

            invitation.accepted_at = (
                datetime.now(UTC)
            )

            self.uow.flush()


            self.uow.refresh(
                invitation,
                relationships=[
                    "business",
                ],
            )


        return invitation