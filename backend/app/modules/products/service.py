from app.db.unit_of_work import UnitOfWork
from app.modules.products.repository import ProductRepository, StockMovementRepository, ProductSaleRepository
from app.modules.products.schemas import ProductCreate, ProductUpdate, ProductSaleCreate, StockAdjustment
from app.modules.products.models import Product, StockMovement, ProductSale
from app.shared.enums.product import ProductStatus, StockMovementType
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
import uuid
from typing import List, Optional, Dict, Any

class ProductService:
    def __init__(
        self,
        product_repo: ProductRepository,
        stock_movement_repo: StockMovementRepository,
        product_sale_repo: ProductSaleRepository,
        uow: UnitOfWork
    ):
        self.product_repo = product_repo
        self.stock_movement_repo = stock_movement_repo
        self.product_sale_repo = product_sale_repo
        self.uow = uow

    def create_product(self, business_id: uuid.UUID, data: ProductCreate) -> Product:
        if data.sku:
            existing = self.product_repo.get_by_sku(business_id, data.sku)
            if existing:
                raise ConflictException("Product with this SKU already exists")
        
        product = Product(
            business_id=business_id,
            **data.model_dump()
        )
        with self.uow:
            self.product_repo.create(product)
            self.uow.flush()
            self.uow.refresh(product)
        return product

    def list_products(
        self, 
        business_id: uuid.UUID, 
        page: int = 1, 
        size: int = 20,
        category: Optional[str] = None,
        status: Optional[ProductStatus] = None,
        search: Optional[str] = None,
        low_stock_only: bool = False
    ) -> List[Product]:
        return self.product_repo.list_by_business(
            business_id=business_id, 
            page=page, 
            size=size,
            category=category,
            status=status,
            search=search,
            low_stock_only=low_stock_only
        )

    def get_product(self, business_id: uuid.UUID, product_id: uuid.UUID) -> Product:
        product = self.product_repo.get_by_business(business_id, product_id)
        if not product:
            raise NotFoundException("Product not found")
        return product

    def update_product(self, business_id: uuid.UUID, product_id: uuid.UUID, data: ProductUpdate) -> Product:
        product = self.get_product(business_id, product_id)
        if data.sku and data.sku != product.sku:
            existing = self.product_repo.get_by_sku(business_id, data.sku)
            if existing:
                raise ConflictException("Product with this SKU already exists")
                
        update_data = data.model_dump(exclude_unset=True)
        with self.uow:
            for key, value in update_data.items():
                setattr(product, key, value)
            self.uow.flush()
            self.uow.refresh(product)
        return product

    def delete_product(self, business_id: uuid.UUID, product_id: uuid.UUID) -> None:
        product = self.get_product(business_id, product_id)
        with self.uow:
            self.product_repo.soft_delete(product)

    def adjust_stock(self, business_id: uuid.UUID, product_id: uuid.UUID, data: StockAdjustment, user_id: uuid.UUID) -> StockMovement:
        product = self.get_product(business_id, product_id)
        
        movement = StockMovement(
            product_id=product.id,
            business_id=business_id,
            branch_id=product.branch_id,
            movement_type=data.movement_type,
            quantity=data.quantity,
            unit_price=data.unit_price,
            total_price=(data.unit_price * abs(data.quantity)) if data.unit_price else None,
            notes=data.notes,
            created_by=user_id
        )

        with self.uow:
            product.current_stock += data.quantity
            if product.current_stock < 0:
                raise BadRequestException("Stock cannot be negative")
            if product.current_stock == 0:
                product.status = ProductStatus.OUT_OF_STOCK
            elif product.status == ProductStatus.OUT_OF_STOCK:
                product.status = ProductStatus.ACTIVE
                
            self.stock_movement_repo.create(movement)
            self.uow.flush()
            self.uow.refresh(movement)
            
        return movement

    def list_stock_movements(self, product_id: uuid.UUID, page: int = 1, size: int = 20) -> List[StockMovement]:
        return self.stock_movement_repo.list_by_product(product_id, page, size)

    def create_sale(self, business_id: uuid.UUID, data: ProductSaleCreate, user_id: uuid.UUID) -> ProductSale:
        items_data = []
        subtotal = 0.0
        tax_amount = 0.0
        
        with self.uow:
            for item in data.items:
                product = self.get_product(business_id, item.product_id)
                if product.current_stock < item.quantity:
                    raise BadRequestException(f"Insufficient stock for product {product.name}")
                    
                item_subtotal = float(product.sale_price) * item.quantity
                item_tax = item_subtotal * float(product.tax_rate) / 100
                
                subtotal += item_subtotal
                tax_amount += item_tax
                
                items_data.append({
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "unit_price": float(product.sale_price),
                    "tax_rate": float(product.tax_rate),
                    "total": item_subtotal + item_tax
                })
                
                product.current_stock -= item.quantity
                if product.current_stock == 0:
                    product.status = ProductStatus.OUT_OF_STOCK
                
                movement = StockMovement(
                    product_id=product.id,
                    business_id=business_id,
                    branch_id=data.branch_id or product.branch_id,
                    movement_type=StockMovementType.SALE,
                    quantity=-item.quantity,
                    unit_price=float(product.sale_price),
                    total_price=item_subtotal,
                    reference_type="SALE",
                    created_by=user_id
                )
                self.stock_movement_repo.create(movement)

            total_amount = subtotal + tax_amount
            
            sale = ProductSale(
                business_id=business_id,
                branch_id=data.branch_id,
                customer_id=data.customer_id,
                items=items_data,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                payment_method=data.payment_method,
                notes=data.notes
            )
            
            self.product_sale_repo.create(sale)
            self.uow.flush()
            
            for movement in self.stock_movement_repo.list_by_business(business_id, page=1, size=len(data.items)):
                if movement.reference_type == "SALE" and movement.reference_id is None:
                    movement.reference_id = sale.id
                    
            self.uow.refresh(sale)
            
        return sale

    def list_sales(self, business_id: uuid.UUID, page: int = 1, size: int = 20) -> List[ProductSale]:
        return self.product_sale_repo.list_by_business(business_id, page, size)

    def get_sale(self, business_id: uuid.UUID, sale_id: uuid.UUID) -> ProductSale:
        sale = self.product_sale_repo.get_by_business(business_id, sale_id)
        if not sale:
            raise NotFoundException("Sale not found")
        return sale

    def get_stock_summary(self, business_id: uuid.UUID) -> Dict[str, Any]:
        products = self.list_products(business_id, size=10000)
        
        total_products = len(products)
        low_stock_count = sum(1 for p in products if p.current_stock <= p.min_stock_level and p.current_stock > 0)
        out_of_stock_count = sum(1 for p in products if p.current_stock <= 0)
        total_stock_value = sum(float(p.purchase_price) * p.current_stock for p in products if p.current_stock > 0)
        
        return {
            "total_products": total_products,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "total_stock_value": total_stock_value
        }
