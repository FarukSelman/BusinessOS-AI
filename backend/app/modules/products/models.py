from sqlalchemy import String, Text, ForeignKey, Integer, Numeric, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.shared.models.base import BaseModel
from app.shared.enums.product import ProductStatus, StockMovementType
from app.shared.enums.invoice import PaymentMethod
from sqlalchemy import func

class Product(BaseModel):
    __tablename__ = "products"

    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(50), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), default="adet")
    
    purchase_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    sale_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=18.0)
    
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    min_stock_level: Mapped[int] = mapped_column(Integer, default=0)
    max_stock_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ProductStatus] = mapped_column(String(50), default=ProductStatus.ACTIVE)


class StockMovement(BaseModel):
    __tablename__ = "stock_movements"

    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True
    )

    movement_type: Mapped[StockMovementType] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class ProductSale(BaseModel):
    __tablename__ = "product_sales"

    business_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )

    sale_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    items: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    
    payment_method: Mapped[PaymentMethod | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
