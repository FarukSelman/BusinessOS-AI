from uuid import UUID

from app.core.exceptions import NotFoundException
from app.db.unit_of_work import UnitOfWork

from app.modules.business.models import Business
from app.modules.business.repository import BusinessRepository
from app.modules.user.models import User
from app.modules.user.repository import UserRepository

from app.shared.enums.business import BusinessStatus
from app.shared.enums.business_plan import BusinessPlan


class AdminService:

    def __init__(
        self,
        business_repository: BusinessRepository,
        user_repository: UserRepository,
        uow: UnitOfWork,
    ):
        self.business_repository = business_repository
        self.user_repository = user_repository
        self.uow = uow

    # --------------------------------------------------
    # Businesses
    # --------------------------------------------------

    def list_businesses(self, page: int = 1, size: int = 20) -> list[Business]:
        return self.business_repository.get_all_paginated(page=page, size=size)

    def get_business(self, business_id: UUID) -> Business:
        business = self.business_repository.get(business_id)
        if not business:
            raise NotFoundException("Business not found.")
        return business

    def update_business_status(self, business_id: UUID, status: BusinessStatus) -> Business:
        business = self.get_business(business_id)
        business.status = status
        with self.uow:
            self.uow.flush()
            self.uow.refresh(business)
        return business

    def update_business_plan(self, business_id: UUID, plan: BusinessPlan) -> Business:
        business = self.get_business(business_id)
        business.plan = plan
        with self.uow:
            self.uow.flush()
            self.uow.refresh(business)
        return business

    def delete_business(self, business_id: UUID) -> None:
        business = self.get_business(business_id)
        with self.uow:
            self.business_repository.delete(business)
            self.uow.flush()

    # --------------------------------------------------
    # Users
    # --------------------------------------------------

    def list_users(self, page: int = 1, size: int = 20) -> list[User]:
        return self.user_repository.get_all_paginated(page=page, size=size)