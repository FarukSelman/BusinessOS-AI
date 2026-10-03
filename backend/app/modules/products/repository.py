from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from app.db.base_repository import BaseRepository
from app.modules.products.models import Product, StockMovement, ProductSale
import uuid
from typing import List, Optional
from app.shared.enums.product import ProductStatus, StockMovementType

class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=Product)

    def list_by_business(
        self,
        business_id: uuid.UUID,
        page: int = 1,
        size: int = 20,
        category: Optional[str] = None,
        status: Optional[ProductStatus] = None,
        search: Optional[str] = None,
        low_stock_only: bool = False
    ) -> List[Product]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )

        if category:
            query = query.where(self.model.category == category)
        if status:
            query = query.where(self.model.status == status)
        if low_stock_only:
            query = query.where(self.model.current_stock <= self.model.min_stock_level)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    self.model.name.ilike(search_term),
                    self.model.sku.ilike(search_term),
                    self.model.barcode.ilike(search_term)
                )
            )

        query = query.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())

    def get_by_business(self, business_id: uuid.UUID, product_id: uuid.UUID) -> Optional[Product]:
        query = select(self.model).where(
            self.model.id == product_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalars(query).first()

    def get_by_sku(self, business_id: uuid.UUID, sku: str) -> Optional[Product]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.sku == sku,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalars(query).first()

    def get_low_stock_products(self, business_id: uuid.UUID) -> List[Product]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.current_stock <= self.model.min_stock_level,
            self.model.is_deleted.is_(False)
        )
        return list(self.db.scalars(query).all())

    def search_products(self, business_id: uuid.UUID, search: str) -> List[Product]:
        search_term = f"%{search}%"
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False),
            or_(
                self.model.name.ilike(search_term),
                self.model.sku.ilike(search_term),
                self.model.barcode.ilike(search_term)
            )
        )
        return list(self.db.scalars(query).all())

class StockMovementRepository(BaseRepository[StockMovement]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=StockMovement)

    def list_by_product(self, product_id: uuid.UUID, page: int = 1, size: int = 20) -> List[StockMovement]:
        query = select(self.model).where(
            self.model.product_id == product_id,
            self.model.is_deleted.is_(False)
        ).order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())

    def list_by_business(
        self, 
        business_id: uuid.UUID, 
        page: int = 1, 
        size: int = 20, 
        movement_type: Optional[StockMovementType] = None
    ) -> List[StockMovement]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        if movement_type:
            query = query.where(self.model.movement_type == movement_type)
            
        query = query.order_by(self.model.created_at.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())


class ProductSaleRepository(BaseRepository[ProductSale]):
    def __init__(self, db: Session):
        super().__init__(db=db, model=ProductSale)

    def list_by_business(
        self,
        business_id: uuid.UUID,
        page: int = 1,
        size: int = 20,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[ProductSale]:
        query = select(self.model).where(
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        if date_from:
            query = query.where(self.model.sale_date >= date_from)
        if date_to:
            query = query.where(self.model.sale_date <= date_to)
            
        query = query.order_by(self.model.sale_date.desc()).offset((page - 1) * size).limit(size)
        return list(self.db.scalars(query).all())

    def get_by_business(self, business_id: uuid.UUID, sale_id: uuid.UUID) -> Optional[ProductSale]:
        query = select(self.model).where(
            self.model.id == sale_id,
            self.model.business_id == business_id,
            self.model.is_deleted.is_(False)
        )
        return self.db.scalars(query).first()
