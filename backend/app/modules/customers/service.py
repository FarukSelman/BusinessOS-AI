from __future__ import annotations

from datetime import date
from uuid import UUID

from app.core.exceptions import (
    NotFoundException,
)
from app.db.unit_of_work import UnitOfWork
from app.modules.customers.models import Customer
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerUpdate,
)


class CustomerService:

    def __init__(
        self,
        repository: CustomerRepository,
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
        data: CustomerCreate,
    ) -> Customer:

        customer = Customer(
            business_id=business_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            notes=data.notes,
        )

        with self.uow:

            self.repository.create(
                customer,
            )

            self.uow.flush()

            self.uow.refresh(
                customer,
            )

        return customer

    # --------------------------------------------------
    # LIST
    # --------------------------------------------------

    def list_filtered(
        self,
        business_id: UUID,
        tag_ids: list[UUID] | None = None,
        status: str | None = None,
        min_visits: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict], int]:
        """One page of customers, each with its tags, and the total count."""
        customers, total = self.repository.list_by_business_filtered(
            business_id=business_id,
            tag_ids=tag_ids,
            status=status,
            min_visits=min_visits,
            date_from=date_from,
            date_to=date_to,
            search=search,
            page=page,
            size=size,
        )
        ids = [c.id for c in customers]
        tags = self.repository.tags_by_customer(ids)
        stats = self.repository.visit_stats(business_id, ids)
        return [{"customer": c, "tags": tags[c.id], **stats[c.id]} for c in customers], total

    def get_detail(self, business_id: UUID, customer_id: UUID) -> dict:
        """One customer with its tags and visit stats (same shape as a list row)."""
        customer = self.get(business_id, customer_id)
        return {
            "customer": customer,
            "tags": self.repository.tags_by_customer([customer.id])[customer.id],
            **self.repository.visit_stats(business_id, [customer.id])[customer.id],
        }

    def get_history(self, business_id: UUID, customer_id: UUID) -> dict:
        self.get(business_id, customer_id)
        from app.modules.appointments.repository import AppointmentRepository
        from app.modules.loyalty.repository import LoyaltyWalletRepository
        from app.modules.customer_tags.repository import CustomerTagAssignmentRepository
        
        appointment_repo = AppointmentRepository(self.repository.db)
        loyalty_repo = LoyaltyWalletRepository(self.repository.db)
        tag_repo = CustomerTagAssignmentRepository(self.repository.db)
        
        customer_appointments = appointment_repo.list_by_customer(business_id, customer_id)
        
        wallet = loyalty_repo.get_by_customer(business_id, customer_id)
        tags = tag_repo.get_tags_for_customer(customer_id)
        
        # Serialised here: the route returns a plain dict, which cannot hold ORM objects.
        from app.modules.appointments.schemas import AppointmentResponse
        from app.modules.customers.schemas import CustomerTagBrief
        from app.modules.loyalty.schemas import LoyaltyWalletResponse

        return {
            "appointments": [AppointmentResponse.model_validate(a).model_dump(mode="json") for a in customer_appointments],
            "loyalty_wallet": LoyaltyWalletResponse.model_validate(wallet).model_dump(mode="json") if wallet else None,
            "tags": [CustomerTagBrief.model_validate(t).model_dump(mode="json") for t in tags],
        }
    # --------------------------------------------------
    # GET
    # --------------------------------------------------

    def get(
        self,
        business_id: UUID,
        customer_id: UUID,
    ) -> Customer:

        customer = self.repository.get_by_business(
            business_id=business_id,
            customer_id=customer_id,
        )

        if customer is None:

            raise NotFoundException(
                "Customer not found.",
            )

        return customer

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update(
        self,
        business_id: UUID,
        customer_id: UUID,
        data: CustomerUpdate,
    ) -> Customer:

        customer = self.get(
            business_id=business_id,
            customer_id=customer_id,
        )

        update_data = data.model_dump(
            exclude_unset=True,
        )

        for key, value in update_data.items():

            setattr(
                customer,
                key,
                value,
            )

        with self.uow:

            self.uow.flush()

            self.uow.refresh(
                customer,
            )

        return customer

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    def delete(
        self,
        business_id: UUID,
        customer_id: UUID,
    ) -> None:

        customer = self.get(
            business_id=business_id,
            customer_id=customer_id,
        )

        with self.uow:

            self.repository.delete(
                customer,
            )
