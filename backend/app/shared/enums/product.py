from enum import Enum

class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"

class StockMovementType(str, Enum):
    PURCHASE = "PURCHASE"    # Satın alma (stok girişi)
    SALE = "SALE"            # Satış (stok çıkışı)
    ADJUSTMENT = "ADJUSTMENT" # Manuel düzeltme
    RETURN = "RETURN"        # İade
    TRANSFER = "TRANSFER"    # Şubeler arası transfer
    WASTE = "WASTE"          # Fire/zayi
