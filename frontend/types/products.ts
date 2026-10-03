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
  purchase_price: number;
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
  items: { product_id: string; product_name: string; quantity: number; unit_price: number; total: number }[];
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  payment_method: string | null;
  sale_date: string;
  notes: string | null;
  created_at: string;
}

export interface StockSummary {
  total_products: number;
  low_stock_count: number;
  out_of_stock_count: number;
  total_stock_value: number;
}
