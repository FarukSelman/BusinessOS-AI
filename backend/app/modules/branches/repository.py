from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.base_repository import BaseRepository
from app.modules.branches.models import Branch

class BranchRepository(BaseRepository[Branch]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Branch)
        
    def list_by_business(self, business_id: UUID, page: int = 1, size: int = 20) -> list[Branch]:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(statement).all())
        
    def get_by_business(self, business_id: UUID, branch_id: UUID) -> Branch | None:
        statement = select(self.model).where(
            self.model.id == branch_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalar(statement)
        
    def get_main_branch(self, business_id: UUID) -> Branch | None:
        statement = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_main.is_(True),
            self.model.is_deleted.is_(False)
        )
        return self.db.scalar(statement)
