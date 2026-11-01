from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any
import uuid
from datetime import datetime
from app.shared.enums.product import ProductStatus, StockMovementType
from app.shared.enums.invoice import PaymentMethod

class ProductCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=50)
    barcode: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field("adet", max_length=20)
    purchase_price: float = 0.0
    sale_price: float = 0.0
    tax_rate: Optional[float] = 18.0
    min_stock_level: Optional[int] = 0
    max_stock_level: Optional[int] = None
    branch_id: Optional[uuid.UUID] = None
    image_url: Optional[str] = Field(None, max_length=500)

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    sku: Optional[str] = Field(None, max_length=50)
    barcode: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=20)
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    tax_rate: Optional[float] = None
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    branch_id: Optional[uuid.UUID] = None
    image_url: Optional[str] = Field(None, max_length=500)
    status: Optional[ProductStatus] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    business_id: uuid.UUID
    branch_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    unit: str
    # Cost: None for roles without finance access (employee, viewer)
    purchase_price: Optional[float]
    sale_price: float
    tax_rate: float
    current_stock: int
    min_stock_level: int
    max_stock_level: Optional[int] = None
    image_url: Optional[str] = None
    status: ProductStatus
    created_at: datetime
    updated_at: datetime

class StockAdjustment(BaseModel):
    quantity: int
    unit_price: Optional[float] = None
    movement_type: StockMovementType
    notes: Optional[str] = None

class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    product_id: uuid.UUID
    movement_type: StockMovementType
    quantity: int
    # None for roles without finance access (purchase/adjustment prices are costs)
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    reference_type: Optional[str] = None
    reference_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    created_at: datetime

class ProductSaleItem(BaseModel):
    product_id: uuid.UUID
    quantity: int

class ProductSaleCreate(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    branch_id: Optional[uuid.UUID] = None
    items: List[ProductSaleItem]
    payment_method: Optional[PaymentMethod] = None
    notes: Optional[str] = None

class ProductSaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    business_id: uuid.UUID
    branch_id: Optional[uuid.UUID] = None
    customer_id: Optional[uuid.UUID] = None
    invoice_id: Optional[uuid.UUID] = None
    sale_date: datetime
    items: List[dict]
    # Turnover: None for roles without finance access (item "total" too; unit_price is the public sale price)
    subtotal: Optional[float]
    tax_amount: Optional[float]
    total_amount: Optional[float]
    payment_method: Optional[PaymentMethod] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class StockSummary(BaseModel):
    total_products: int
    low_stock_count: int
    out_of_stock_count: int
    # purchase_price x stock: None for roles without finance access
    total_stock_value: Optional[float]


# ---------------------------------------------------------------- role views
# Same rule as invoices: owner/admin see costs and turnover, other roles get
# None for those fields. Sale prices stay visible (customers see them).

def product_view(product, show_amounts: bool) -> ProductResponse:
    view = ProductResponse.model_validate(product)
    return view if show_amounts else view.model_copy(update={"purchase_price": None})


def movement_view(movement, show_amounts: bool) -> StockMovementResponse:
    view = StockMovementResponse.model_validate(movement)
    return view if show_amounts else view.model_copy(update={"unit_price": None, "total_price": None})


def sale_view(sale, show_amounts: bool) -> ProductSaleResponse:
    view = ProductSaleResponse.model_validate(sale)
    if show_amounts:
        return view
    return view.model_copy(update={
        "subtotal": None,
        "tax_amount": None,
        "total_amount": None,
        "items": [{**item, "total": None} for item in view.items],
    })


def stock_summary_view(summary: dict, show_amounts: bool) -> StockSummary:
    view = StockSummary(**summary)
    return view if show_amounts else view.model_copy(update={"total_stock_value": None})
