from uuid import UUID, uuid4
from typing import List

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.business.models import Business
from app.modules.business.repository import BusinessRepository
from app.modules.business.schemas import (
    BusinessCreate,
    BusinessUpdate,
)
from app.shared.utils.slug import generate_slug
from app.modules.membership.models import Membership
from app.modules.membership.repository import MembershipRepository
from app.shared.enums.membership import MembershipRole


class BusinessService:

    def __init__(
        self,
        repository: BusinessRepository,
        membership_repository: MembershipRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.membership_repository = membership_repository
        self.uow = uow

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    def create(
        self,
        data: BusinessCreate,
        user_id: UUID,
    ) -> Business:

        # Same names are common ("Kuaför"): add -2, -3 ... instead of refusing.
        base_slug = generate_slug(
            data.name,
        ) or "isletme"
        slug = base_slug
        for suffix in range(2, 52):
            if not self.repository.exists_by_slug(
                slug,
            ):
                break
            slug = f"{base_slug}-{suffix}"
        else:
            slug = f"{base_slug}-{uuid4().hex[:6]}"  # bounded: never loop forever
        
        if self.repository.exists_by_email(
            data.email,
        ):
            raise ConflictException(
                "Business email already exists.",
            )

        business = Business(
            name=data.name,
            slug=slug,
            industry=data.industry,
            email=data.email,
            phone=data.phone,
            website=str(data.website) if data.website else None,
            logo_url=str(data.logo_url) if data.logo_url else None,
        )

        with self.uow:

            self.repository.create(
                business,
            )

            self.uow.flush()

            membership = Membership(
                user_id=user_id,
                business_id=business.id,
                role=MembershipRole.OWNER,
            )

            self.membership_repository.create(
                membership,
            )

            self.uow.flush()

            self.uow.refresh(
                business,
            )

        return business

    # --------------------------------------------------
    # LIST
    # --------------------------------------------------

    def list(
        self,
        page: int = 1,
        size: int = 20,
    ) -> List[Business]:

        return self.repository.list_paginated(
            page=page,
            size=size,
        )

    #--------------------------------------------------
    # LIST FOR USER
    #--------------------------------------------------
    def list_for_user(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> List[Business]:
        """Sadece kullanıcının üye olduğu işletmeleri döndürür (list() tüm sistemi döndürüyordu)."""
        memberships = self.membership_repository.get_user_memberships(
            user_id=user_id,
            page=page,
            size=size,
        )
        return [membership.business for membership in memberships]

    # --------------------------------------------------
    # GET
    # --------------------------------------------------

    def get(
        self,
        business_id: UUID,
    ) -> Business:

        business = self.repository.get(
            business_id,
        )

        if business is None:

            raise NotFoundException(
                "Business not found.",
            )

        return business

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update(
        self,
        business_id: UUID,
        data: BusinessUpdate,
    ) -> Business:

        business = self.get(
            business_id,
        )

        update_data = data.model_dump(
            exclude_unset=True,
        )

        if "slug" in update_data:

            existing = self.repository.get_by_slug(
                update_data["slug"],
            )

            if existing and existing.id != business.id:

                raise ConflictException(
                    "Business slug already exists.",
                )

        for key, value in update_data.items():

            if key in ["website", "logo_url"] and value:
                value = str(value)

            setattr(
                business,
                key,
                value,
            )

        with self.uow:

            self.uow.flush()

            self.uow.refresh(
                business,
            )

        return business

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    def delete(
        self,
        business_id: UUID,
    ) -> None:

        business = self.get(
            business_id,
        )

        with self.uow:

            self.repository.delete(
                business,
            )