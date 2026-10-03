from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundException
from app.db.unit_of_work import UnitOfWork
from app.modules.services.models import Service
from app.modules.services.repository import ServiceRepository
from app.modules.services.schemas import (
    ServiceCreate,
    ServiceUpdate,
)


class ServiceService:

    def __init__(
        self,
        repository: ServiceRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    def create(
        self,
        business_id: UUID,
        data: ServiceCreate,
    ) -> Service:

        service = Service(
            business_id=business_id,
            name=data.name,
            description=data.description,
            price=data.price,
            duration_minutes=data.duration_minutes,
            category=data.category,
        )

        with self.uow:

            self.repository.create(
                service,
            )

            self.uow.flush()

            self.uow.refresh(
                service,
            )

        return service

    # --------------------------------------------------
    # LIST
    # --------------------------------------------------

    def list(
        self,
        business_id: UUID,
        page: int = 1,
        size: int = 50,
    ) -> list[Service]:

        return self.repository.list_by_business(
            business_id,
            page=page,
            size=size,
        )

    # --------------------------------------------------
    # GET
    # --------------------------------------------------

    def get(
        self,
        business_id: UUID,
        service_id: UUID,
    ) -> Service:

        service = self.repository.get_by_business(
            business_id,
            service_id,
        )

        if service is None:

            raise NotFoundException(
                "Service not found.",
            )

        return service

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update(
        self,
        business_id: UUID,
        service_id: UUID,
        data: ServiceUpdate,
    ) -> Service:

        service = self.get(
            business_id,
            service_id,
        )

        update_data = data.model_dump(
            exclude_unset=True,
        )

        for key, value in update_data.items():
            setattr(
                service,
                key,
                value,
            )

        with self.uow:

            self.uow.flush()

            self.uow.refresh(
                service,
            )

        return service

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    def delete(
        self,
        business_id: UUID,
        service_id: UUID,
    ) -> None:

        service = self.get(
            business_id,
            service_id,
        )

        with self.uow:

            self.repository.delete(
                service,
            )

    # --------------------------------------------------
    # LIST ACTIVE
    # --------------------------------------------------

    def list_active(
        self,
        business_id: UUID,
    ) -> list[Service]:

        return self.repository.list_active_by_business(
            business_id,
        )

    # --------------------------------------------------
    # LIST BY CATEGORY
    # --------------------------------------------------

    def list_by_category(
        self,
        business_id: UUID,
        category: str,
    ) -> list[Service]:

        return self.repository.list_by_category(
            business_id,
            category,
        )
