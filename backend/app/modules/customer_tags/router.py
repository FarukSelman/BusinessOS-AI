from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.modules.customer_tags.schemas import TagCreate, TagUpdate, TagResponse, TagAssignmentCreate
from app.modules.customer_tags.repository import CustomerTagRepository, CustomerTagAssignmentRepository
from app.modules.customer_tags.service import CustomerTagService

router = APIRouter(prefix="/businesses/{business_id}/customer-tags", tags=["Customer Tags"])

def get_service(db: Session = Depends(get_db)) -> CustomerTagService:
    tag_repo = CustomerTagRepository(db)
    assign_repo = CustomerTagAssignmentRepository(db)
    uow = UnitOfWork(db)
    return CustomerTagService(tag_repository=tag_repo, assignment_repository=assign_repo, uow=uow)

@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    business_id: UUID,
    data: TagCreate,
    service: CustomerTagService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.create_tag(business_id=business_id, data=data)

@router.get("", response_model=List[TagResponse])
def list_tags(
    business_id: UUID,
    service: CustomerTagService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_tags(business_id=business_id)

@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(
    business_id: UUID,
    tag_id: UUID,
    data: TagUpdate,
    service: CustomerTagService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.update_tag(business_id=business_id, tag_id=tag_id, data=data)

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    business_id: UUID,
    tag_id: UUID,
    service: CustomerTagService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    service.delete_tag(business_id=business_id, tag_id=tag_id)

@router.post("/customers/{customer_id}/assign", status_code=status.HTTP_201_CREATED)
def assign_tag(
    business_id: UUID,
    customer_id: UUID,
    data: TagAssignmentCreate,
    service: CustomerTagService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    service.assign_tag(business_id=business_id, customer_id=customer_id, tag_id=data.tag_id)
    return {"message": "Tag assigned successfully"}

@router.delete("/customers/{customer_id}/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag(
    business_id: UUID,
    customer_id: UUID,
    tag_id: UUID,
    service: CustomerTagService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    service.remove_tag(business_id=business_id, customer_id=customer_id, tag_id=tag_id)

@router.get("/customers/{customer_id}/tags", response_model=List[TagResponse])
def get_customer_tags(
    business_id: UUID,
    customer_id: UUID,
    service: CustomerTagService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_customer_tags(business_id=business_id, customer_id=customer_id)
