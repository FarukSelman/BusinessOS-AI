export type InvoiceStatus = 'DRAFT' | 'SENT' | 'PAID' | 'OVERDUE' | 'CANCELLED';
export type PaymentMethod = 'CASH' | 'CREDIT_CARD' | 'BANK_TRANSFER' | 'OTHER';

export interface InvoiceItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface Invoice {
  id: string;
  business_id: string;
  customer_id: string | null;
  customer_name: string;
  customer_email: string | null;
  appointment_id: string | null;
  invoice_number: string;
  items: InvoiceItem[];
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  total_amount: number;
  status: InvoiceStatus;
  payment_method: PaymentMethod | null;
  paid_at: string | null;
  due_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvoiceCreatePayload {
  customer_id?: string | null;
  customer_name: string;
  customer_email?: string | null;
  appointment_id?: string | null;
  items: InvoiceItem[];
  subtotal: number;
  tax_rate?: number;
  tax_amount: number;
  total_amount: number;
  status?: InvoiceStatus;
  due_date?: string | null;
  notes?: string | null;
}

export interface InvoiceUpdatePayload {
  customer_name?: string;
  customer_email?: string | null;
  items?: InvoiceItem[];
  subtotal?: number;
  tax_rate?: number;
  tax_amount?: number;
  total_amount?: number;
  status?: InvoiceStatus;
  due_date?: string | null;
  notes?: string | null;
}

export interface RevenueStats {
  total_revenue: number;
  paid_count: number;
  pending_count: number;
  overdue_count: number;
}
