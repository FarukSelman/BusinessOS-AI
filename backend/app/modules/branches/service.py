from uuid import UUID
from app.core.exceptions import NotFoundException
from app.db.unit_of_work import UnitOfWork
from app.modules.branches.models import Branch
from app.modules.branches.repository import BranchRepository
from app.modules.branches.schemas import BranchCreate, BranchUpdate

class BranchService:
    def __init__(self, repository: BranchRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow
        
    def list_branches(self, business_id: UUID, page: int = 1, size: int = 20) -> list[Branch]:
        return self.repository.list_by_business(business_id=business_id, page=page, size=size)
        
    def get_branch(self, business_id: UUID, branch_id: UUID) -> Branch:
        branch = self.repository.get_by_business(business_id=business_id, branch_id=branch_id)
        if not branch:
            raise NotFoundException("Branch not found")
        return branch
        
    def create_branch(self, business_id: UUID, data: BranchCreate) -> Branch:
        branch_data = data.model_dump()
        
        # If this is the first branch, make it main
        existing_branches = self.repository.list_by_business(business_id=business_id, size=1)
        if not existing_branches:
            branch_data["is_main"] = True
            
        with self.uow:
            # If setting as main, ensure no other main branch
            if branch_data.get("is_main"):
                main_branch = self.repository.get_main_branch(business_id)
                if main_branch:
                    main_branch.is_main = False
                    
            branch = Branch(business_id=business_id, **branch_data)
            self.repository.create(branch)
            self.uow.flush()
            self.uow.refresh(branch)
            return branch
            
    def update_branch(self, business_id: UUID, branch_id: UUID, data: BranchUpdate) -> Branch:
        branch = self.get_branch(business_id=business_id, branch_id=branch_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        with self.uow:
            # Handle main branch change
            if update_data.get("is_main") is True and not branch.is_main:
                main_branch = self.repository.get_main_branch(business_id)
                if main_branch and main_branch.id != branch.id:
                    main_branch.is_main = False
            
            # Prevent unsetting main branch without setting another
            if update_data.get("is_main") is False and branch.is_main:
                del update_data["is_main"]
                
            for key, value in update_data.items():
                setattr(branch, key, value)
                
            self.uow.flush()
            self.uow.refresh(branch)
            return branch
            
    def set_main_branch(self, business_id: UUID, branch_id: UUID) -> Branch:
        branch = self.get_branch(business_id=business_id, branch_id=branch_id)
        if branch.is_main:
            return branch
            
        with self.uow:
            main_branch = self.repository.get_main_branch(business_id)
            if main_branch:
                main_branch.is_main = False
            
            branch.is_main = True
            self.uow.flush()
            self.uow.refresh(branch)
            return branch
            
    def delete_branch(self, business_id: UUID, branch_id: UUID) -> None:
        branch = self.get_branch(business_id=business_id, branch_id=branch_id)
        
        with self.uow:
            self.repository.soft_delete(branch)
            # If main branch deleted, try to set another one
            if branch.is_main:
                branches = self.repository.list_by_business(business_id=business_id, size=1)
                if branches:
                    branches[0].is_main = True
            self.uow.flush()
