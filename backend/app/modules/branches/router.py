from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.branches.repository import BranchRepository
from app.modules.branches.schemas import BranchCreate, BranchResponse, BranchUpdate
from app.modules.branches.service import BranchService
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
from app.shared.security.business import require_business_member

router = APIRouter(prefix="/businesses/{business_id}/branches", tags=["Branches"], dependencies=[Depends(require_business_member)])

def get_service(db: Session = Depends(get_db)) -> BranchService:
    repository = BranchRepository(db)
    uow = UnitOfWork(db)
    return BranchService(repository=repository, uow=uow)

@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(
    business_id: UUID,
    data: BranchCreate,
    service: BranchService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.create_branch(business_id=business_id, data=data)

@router.get("", response_model=list[BranchResponse])
def list_branches(
    business_id: UUID,
    page: int = 1,
    size: int = 20,
    service: BranchService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_branches(business_id=business_id, page=page, size=size)

@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(
    business_id: UUID,
    branch_id: UUID,
    service: BranchService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_branch(business_id=business_id, branch_id=branch_id)

@router.patch("/{branch_id}", response_model=BranchResponse)
def update_branch(
    business_id: UUID,
    branch_id: UUID,
    data: BranchUpdate,
    service: BranchService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.update_branch(business_id=business_id, branch_id=branch_id, data=data)

@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branch(
    business_id: UUID,
    branch_id: UUID,
    service: BranchService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    service.delete_branch(business_id=business_id, branch_id=branch_id)

@router.post("/{branch_id}/set-main", response_model=BranchResponse)
def set_main_branch(
    business_id: UUID,
    branch_id: UUID,
    service: BranchService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    return service.set_main_branch(business_id=business_id, branch_id=branch_id)
