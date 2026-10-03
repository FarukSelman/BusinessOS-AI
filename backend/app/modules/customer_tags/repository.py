from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.customer_tags.models import CustomerTag, CustomerTagAssignment
from app.modules.customers.models import Customer

class CustomerTagRepository(BaseRepository[CustomerTag]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=CustomerTag)
        
    def list_by_business(self, business_id: UUID) -> List[CustomerTag]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.created_at.desc())
        return list(self.db.scalars(statement).all())
        
    def count_customers_per_tag(self, business_id: UUID) -> dict:
        from sqlalchemy import func
        from app.modules.customer_tags.models import CustomerTagAssignment
        rows = self.db.execute(
            select(CustomerTagAssignment.tag_id, func.count(CustomerTagAssignment.id))
            .join(self.model, self.model.id == CustomerTagAssignment.tag_id)
            .where(
                self.model.business_id == business_id,
                self.model.is_deleted.is_(False),
                CustomerTagAssignment.is_deleted.is_(False),
            )
            .group_by(CustomerTagAssignment.tag_id)
        ).all()
        return {tag_id: count for tag_id, count in rows}

    def list_customers_with_tag(self, business_id: UUID, tag_id: UUID, limit: int = 20) -> list:
        from app.modules.customer_tags.models import CustomerTagAssignment
        from app.modules.customers.models import Customer
        return list(self.db.scalars(
            select(Customer)
            .join(CustomerTagAssignment, CustomerTagAssignment.customer_id == Customer.id)
            .where(
                Customer.business_id == business_id,
                Customer.is_deleted.is_(False),
                CustomerTagAssignment.tag_id == tag_id,
                CustomerTagAssignment.is_deleted.is_(False),
            )
            .order_by(Customer.name)
            .limit(limit)
        ).all())

    def get_by_business(self, business_id: UUID, tag_id: UUID) -> CustomerTag | None:
        statement = select(self.model).where(
            self.model.id == tag_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalar(statement)

class CustomerTagAssignmentRepository(BaseRepository[CustomerTagAssignment]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=CustomerTagAssignment)

    def get_tags_for_customer(self, customer_id: UUID) -> List[CustomerTag]:
        statement = select(CustomerTag).join(
            CustomerTagAssignment, CustomerTag.id == CustomerTagAssignment.tag_id
        ).where(
            CustomerTagAssignment.customer_id == customer_id,
            CustomerTagAssignment.is_deleted.is_(False),
            CustomerTag.is_deleted.is_(False)
        )
        return list(self.db.scalars(statement).all())

    def get_customers_by_tag(self, tag_id: UUID) -> List[Customer]:
        statement = select(Customer).join(
            CustomerTagAssignment, Customer.id == CustomerTagAssignment.customer_id
        ).where(
            CustomerTagAssignment.tag_id == tag_id,
            CustomerTagAssignment.is_deleted.is_(False),
            Customer.is_deleted.is_(False)
        )
        return list(self.db.scalars(statement).all())
        
    def assign_tag(self, customer_id: UUID, tag_id: UUID) -> CustomerTagAssignment | None:
        statement = select(self.model).where(
            self.model.customer_id == customer_id,
            self.model.tag_id == tag_id,
            self.model.is_deleted.is_(False)
        )
        existing = self.db.scalar(statement)
        if existing:
            return existing
            
        assignment = CustomerTagAssignment(customer_id=customer_id, tag_id=tag_id)
        self.db.add(assignment)
        return assignment
        
    def remove_tag(self, customer_id: UUID, tag_id: UUID) -> bool:
        statement = select(self.model).where(
            self.model.customer_id == customer_id,
            self.model.tag_id == tag_id,
            self.model.is_deleted.is_(False)
        )
        existing = self.db.scalar(statement)
        if existing:
            existing.is_deleted = True
            return True
        return False
