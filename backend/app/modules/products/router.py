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
    ProductSaleCreate, ProductSaleResponse, StockSummary,
    product_view, movement_view, sale_view, stock_summary_view,
)
from app.modules.products.repository import ProductRepository, StockMovementRepository, ProductSaleRepository
from app.modules.products.service import ProductService
from app.shared.enums.product import ProductStatus
from app.ai.agents.tools.common import can_view_finance
from app.modules.membership.models import Membership
from app.shared.security.business import (
    get_business_membership,
    require_business_member,
    require_finance,
    require_staff,
)

# Reading: every member; purchase prices, stock value, movement prices and sale
# turnover are None for roles without finance access. Writing: catalogue and
# stock (costs) for owner/admin, selling for everyone but viewers.

products_router = APIRouter(prefix="/businesses/{business_id}/products", tags=["Products"], dependencies=[Depends(require_business_member)])
product_sales_router = APIRouter(prefix="/businesses/{business_id}/product-sales", tags=["Product Sales"], dependencies=[Depends(require_business_member)])

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
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    return product_view(service.create_product(business_id, data), True)

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
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    show = can_view_finance(membership.role)
    products = service.list_products(business_id, page, size, category, status, search, low_stock_only)
    return [product_view(p, show) for p in products]

@products_router.get("/stock-summary", response_model=StockSummary)
def get_stock_summary(
    business_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    return stock_summary_view(service.get_stock_summary(business_id), can_view_finance(membership.role))

@products_router.get("/low-stock", response_model=List[ProductResponse])
def get_low_stock_products(
    business_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    show = can_view_finance(membership.role)
    return [product_view(p, show) for p in service.list_products(business_id, page=1, size=1000, low_stock_only=True)]

@products_router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    return product_view(service.get_product(business_id, product_id), can_view_finance(membership.role))

@products_router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    data: ProductUpdate,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    return product_view(service.update_product(business_id, product_id, data), True)

@products_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    service.delete_product(business_id, product_id)

@products_router.post("/{product_id}/stock", response_model=StockMovementResponse)
def adjust_stock(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    data: StockAdjustment,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
    _finance: Membership = Depends(require_finance),
):
    return movement_view(service.adjust_stock(business_id, product_id, data, current_user.id), True)

@products_router.get("/{product_id}/movements", response_model=List[StockMovementResponse])
def list_stock_movements(
    business_id: uuid.UUID,
    product_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    # Verify product belongs to business
    service.get_product(business_id, product_id)
    show = can_view_finance(membership.role)
    return [movement_view(m, show) for m in service.list_stock_movements(product_id, page, size)]

# ================================
# Product Sales
# ================================

@product_sales_router.post("", response_model=ProductSaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(
    business_id: uuid.UUID,
    data: ProductSaleCreate,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(require_staff),
):
    sale = service.create_sale(business_id, data, current_user.id)
    return sale_view(sale, can_view_finance(membership.role))

@product_sales_router.get("", response_model=List[ProductSaleResponse])
def list_sales(
    business_id: uuid.UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    show = can_view_finance(membership.role)
    return [sale_view(s, show) for s in service.list_sales(business_id, page, size)]

@product_sales_router.get("/{sale_id}", response_model=ProductSaleResponse)
def get_sale(
    business_id: uuid.UUID,
    sale_id: uuid.UUID,
    service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_user),
    membership: Membership = Depends(get_business_membership),
):
    return sale_view(service.get_sale(business_id, sale_id), can_view_finance(membership.role))
