from uuid import UUID
from app.db.unit_of_work import UnitOfWork
from app.modules.expense_categories.repository import ExpenseCategoryRepository
from app.modules.expense_categories.models import ExpenseCategory
from app.modules.expense_categories.schemas import ExpenseCategoryCreate, ExpenseCategoryUpdate
from app.core.exceptions import NotFoundException

class ExpenseCategoryService:
    def __init__(self, repository: ExpenseCategoryRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    def seed_defaults(self, business_id: UUID) -> None:
        defaults = [
            {"name": "Kira", "color": "#3b82f6", "icon": "home"},
            {"name": "Faturalar", "color": "#eab308", "icon": "zap"},
            {"name": "Malzeme", "color": "#22c55e", "icon": "package"},
            {"name": "Personel", "color": "#a855f7", "icon": "users"},
            {"name": "Pazarlama", "color": "#ec4899", "icon": "megaphone"},
            {"name": "Diğer", "color": "#64748b", "icon": "box"},
        ]
        existing = self.repository.list_by_business(business_id)
        existing_names = {c.name for c in existing}

        to_add = []
        for d in defaults:
            if d["name"] not in existing_names:
                obj = ExpenseCategory(
                    business_id=business_id,
                    name=d["name"],
                    color=d["color"],
                    icon=d["icon"],
                    is_default=True
                )
                to_add.append(obj)
        
        if to_add:
            with self.uow:
                for obj in to_add:
                    self.repository.create(obj)
                self.uow.flush()

    def list_categories(self, business_id: UUID) -> list[ExpenseCategory]:
        return self.repository.list_by_business(business_id)

    def create(self, business_id: UUID, data: ExpenseCategoryCreate) -> ExpenseCategory:
        obj = ExpenseCategory(
            business_id=business_id,
            name=data.name,
            color=data.color,
            icon=data.icon,
            is_default=False
        )
        with self.uow:
            self.repository.create(obj)
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def update(self, business_id: UUID, category_id: UUID, data: ExpenseCategoryUpdate) -> ExpenseCategory:
        obj = self.repository.get_by_business(business_id, category_id)
        if not obj:
            raise NotFoundException("Category not found")
        with self.uow:
            if data.name is not None:
                obj.name = data.name
            if data.color is not None:
                obj.color = data.color
            if data.icon is not None:
                obj.icon = data.icon
            self.uow.flush()
            self.uow.refresh(obj)
        return obj

    def delete(self, business_id: UUID, category_id: UUID) -> None:
        obj = self.repository.get_by_business(business_id, category_id)
        if not obj:
            raise NotFoundException("Category not found")
        with self.uow:
            self.repository.soft_delete(obj)
            self.uow.flush()
