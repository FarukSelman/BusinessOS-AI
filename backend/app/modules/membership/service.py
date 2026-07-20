from uuid import UUID

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
)

from app.db.unit_of_work import UnitOfWork

from app.modules.membership.models import Membership
from app.modules.membership.repository import MembershipRepository
from app.modules.membership.schemas import (
    MembershipCreate,
    MembershipUpdate,
)


class MembershipService:


    def __init__(
        self,
        repository: MembershipRepository,
        uow: UnitOfWork,
    ):

        self.repository = repository
        self.uow = uow



    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    def create_membership(
        self,
        business_id: UUID,
        data: MembershipCreate,
    ) -> Membership:


        if self.repository.exists_by_user_and_business(
            data.user_id,
            business_id,
        ):

            raise ConflictException(
                "User is already a member of this business.",
            )


        membership = Membership(
            user_id=data.user_id,
            business_id=business_id,
            role=data.role,
        )


        with self.uow:

            self.repository.create(
                membership,
            )

            self.uow.flush()

            self.uow.refresh(
                membership,
                relationships=[
                    "user",
                    "business",
                ],
            )


        return membership



    # --------------------------------------------------
    # USER MEMBERSHIPS
    # --------------------------------------------------

    def get_user_memberships(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[Membership]:


        return self.repository.get_user_memberships(
            user_id=user_id,
            page=page,
            size=size,
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


        return self.repository.get_business_memberships(
            business_id=business_id,
            page=page,
            size=size,
        )



    # --------------------------------------------------
    # GET MEMBERSHIP
    # --------------------------------------------------

    def get(
        self,
        membership_id: UUID,
    ) -> Membership:


        membership = self.repository.get(
            membership_id,
        )


        if membership is None:

            raise NotFoundException(
                "Membership not found.",
            )


        return membership

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    def delete(
        self,
        business_id: UUID,
        membership_id: UUID,
    ) -> None:

        membership = self.get(
            membership_id,
        )

        if membership.business_id != business_id:

            raise NotFoundException(
                "Membership not found.",
            )

        if membership.role.name == "OWNER":

            owner_count = self.repository.count_owners(
                business_id,
            )

            if owner_count <= 1:

                raise ConflictException(
                    "Cannot remove the last owner.",
                )

        with self.uow:

            self.repository.delete(
                membership,
            )

    
    # --------------------------------------------------
    # UPDATE MEMBERSHIP ROLE
    # --------------------------------------------------

    def update_membership(
        self,
        business_id: UUID,
        membership_id: UUID,
        data: MembershipUpdate,
    ) -> Membership:


        membership = self.repository.get_by_business_and_id(
            business_id=business_id,
            membership_id=membership_id,
        )


        if membership is None:

            raise NotFoundException(
                "Membership not found.",
            )


        with self.uow:

            membership.role = data.role

            self.uow.flush()

            self.uow.refresh(
                membership,
                relationships=[
                    "user",
                    "business",
                ],
            )


        return membership