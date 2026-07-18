from app.core.exceptions import BadRequestException

from app.modules.membership.models import Membership
from app.modules.membership.repository import MembershipRepository
from app.modules.membership.schemas import MembershipCreate


class MembershipService:

    def __init__(
        self,
        repository: MembershipRepository,
    ):
        self.repository = repository

    def create_membership(
        self,
        data: MembershipCreate,
    ) -> Membership:

        existing = self.repository.get_by_user_and_business(
            data.user_id,
            data.business_id,
        )

        if existing:

            raise BadRequestException(
                "User is already a member of this business."
            )

        membership = Membership(
            user_id=data.user_id,
            business_id=data.business_id,
            role=data.role,
        )

        return self.repository.create(
            membership
        )

    def get_user_memberships(
        self,
        user_id,
    ):
        return self.repository.get_user_memberships(
            user_id
        )

    def get_business_memberships(
        self,
        business_id,
    ):
        return self.repository.get_business_memberships(
            business_id
        )