from uuid import UUID
from typing import List
from app.db.unit_of_work import UnitOfWork
from app.core.exceptions import NotFoundException, BadRequestException
from app.modules.customer_tags.models import CustomerTag, CustomerTagAssignment
from app.modules.customer_tags.repository import CustomerTagRepository, CustomerTagAssignmentRepository
from app.modules.customer_tags.schemas import TagCreate, TagUpdate

class CustomerTagService:
    def __init__(self, tag_repository: CustomerTagRepository, assignment_repository: CustomerTagAssignmentRepository, uow: UnitOfWork):
        self.tag_repository = tag_repository
        self.assignment_repository = assignment_repository
        self.uow = uow
        
    def create_tag(self, business_id: UUID, data: TagCreate) -> CustomerTag:
        tag = CustomerTag(business_id=business_id, **data.model_dump(exclude_unset=True))
        with self.uow:
            self.tag_repository.create(tag)
            self.uow.flush()
            self.uow.refresh(tag)
        return tag

    def list_tags(self, business_id: UUID) -> List[CustomerTag]:
        return self.tag_repository.list_by_business(business_id)
        
    def update_tag(self, business_id: UUID, tag_id: UUID, data: TagUpdate) -> CustomerTag:
        tag = self.tag_repository.get_by_business(business_id, tag_id)
        if not tag:
            raise NotFoundException("Tag not found")
            
        with self.uow:
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(tag, key, value)
            self.uow.flush()
            self.uow.refresh(tag)
        return tag
        
    def delete_tag(self, business_id: UUID, tag_id: UUID):
        tag = self.tag_repository.get_by_business(business_id, tag_id)
        if not tag:
            raise NotFoundException("Tag not found")
            
        with self.uow:
            self.tag_repository.soft_delete(tag_id)
            
    def assign_tag(self, business_id: UUID, customer_id: UUID, tag_id: UUID) -> None:
        tag = self.tag_repository.get_by_business(business_id, tag_id)
        if not tag:
            raise NotFoundException("Tag not found")
            
        with self.uow:
            self.assignment_repository.assign_tag(customer_id, tag_id)
            
    def remove_tag(self, business_id: UUID, customer_id: UUID, tag_id: UUID) -> None:
        with self.uow:
            removed = self.assignment_repository.remove_tag(customer_id, tag_id)
            if not removed:
                raise NotFoundException("Tag assignment not found")
                
    def get_customer_tags(self, business_id: UUID, customer_id: UUID) -> List[CustomerTag]:
        return self.assignment_repository.get_tags_for_customer(customer_id)
