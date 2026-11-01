export type ProductStatus = 'ACTIVE' | 'INACTIVE' | 'OUT_OF_STOCK';
export type StockMovementType = 'PURCHASE' | 'SALE' | 'ADJUSTMENT' | 'RETURN' | 'TRANSFER' | 'WASTE';

export interface Product {
  id: string;
  business_id: string;
  branch_id: string | null;
  name: string;
  description: string | null;
  sku: string | null;
  barcode: string | null;
  category: string | null;
  brand: string | null;
  unit: string;
  /** Alış fiyatı (maliyet): çalışan/izleyici rolünde null. */
  purchase_price: number | null;
  sale_price: number;
  tax_rate: number;
  current_stock: number;
  min_stock_level: number;
  max_stock_level: number | null;
  image_url: string | null;
  status: ProductStatus;
  created_at: string;
  updated_at: string;
}

export interface StockMovement {
  id: string;
  product_id: string;
  movement_type: StockMovementType;
  quantity: number;
  unit_price: number | null;
  total_price: number | null;
  reference_type: string | null;
  notes: string | null;
  created_at: string;
}

export interface ProductSale {
  id: string;
  business_id: string;
  customer_id: string | null;
  /** unit_price satış fiyatıdır, her rolde gelir; total ve tutarlar çalışan/izleyicide null. */
  items: { product_id: string; product_name: string; quantity: number; unit_price: number; total: number | null }[];
  subtotal: number | null;
  tax_amount: number | null;
  total_amount: number | null;
  payment_method: string | null;
  sale_date: string;
  notes: string | null;
  created_at: string;
}

export interface StockSummary {
  total_products: number;
  low_stock_count: number;
  out_of_stock_count: number;
  /** Alış fiyatı × stok: çalışan/izleyici rolünde null. */
  total_stock_value: number | null;
}
