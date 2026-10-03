from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.unit_of_work import UnitOfWork
from app.modules.user.models import User
from app.shared.security.dependencies import get_current_user
import uuid
from typing import List, Optional

from app.modules.products.schemas import (
    ProductCreate, ProductUpdate, ProductResponse,
    StockAdjustment, StockMovementResponse,
    ProductSaleCreate, ProductSaleResponse, StockSummary
)
from app.modules.products.repository import ProductRepository, StockMovementRepository, ProductSaleRepository
from app.modules.products.service import ProductService
from app.shared.enums.product import ProductStatus

products_router = APIRouter(prefix="/businesses/{business_id}/products", tags=["Products"])
product_sales_router = APIRouter(prefix="/businesses/{business_id}/product-sales", tags=["Product Sales"])

def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    product_repo = ProductRepository(db)
    stock_movement_repo = StockMovementRepository(db)
    product_sale_repo = ProductSaleRepository(db)
    uow = UnitOfWork(db)
    return ProductService(product_repo, stock_movement_repo, product_sale_repo, uow)

# ================================
# Products
# ================================

@products_router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    business_id: uuid.UUID,
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    return service.create_product(business_id, data)

@products_router.get("", response_model=List[ProductResponse])
def list_products(
    business_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    category: Optional[str] = None,
    status: Optional[ProductStatus] = None,
    search: Optional[str] = None,
    low_stock_only: bool = False,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_products(
        business_id, page, size, category, status, search, low_stock_only
    )

@products_router.get("/stock-summary", response_model=StockSummary)
def get_stock_summary(
    business_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_stock_summary(business_id)

@products_router.get("/low-stock", response_model=List[ProductResponse])
def get_low_stock_products(
    business_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_products(business_id, page=1, size=1000, low_stock_only=True)

@products_router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_product(business_id, product_id)

@products_router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    data: ProductUpdate,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    return service.update_product(business_id, product_id, data)

@products_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    service.delete_product(business_id, product_id)

@products_router.post("/{product_id}/stock", response_model=StockMovementResponse)
def adjust_stock(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    data: StockAdjustment,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    return service.adjust_stock(business_id, product_id, data, current_user.id)

@products_router.get("/{product_id}/movements", response_model=List[StockMovementResponse])
def list_stock_movements(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    # Verify product belongs to business
    service.get_product(business_id, product_id)
    return service.list_stock_movements(product_id, page, size)

# ================================
# Product Sales
# ================================

@product_sales_router.post("", response_model=ProductSaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    business_id: uuid.UUID,
    data: ProductSaleCreate,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    return service.create_sale(business_id, data, current_user.id)

@product_sales_router.get("", response_model=List[ProductSaleResponse])
def list_sales(
    business_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    return service.list_sales(business_id, page, size)

@product_sales_router.get("/{sale_id}", response_model=ProductSaleResponse)
def get_sale(
    business_id: uuid.UUID,
    sale_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user)
):
    return service.get_sale(business_id, sale_id)
