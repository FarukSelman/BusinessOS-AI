import type { AppointmentStatus } from "./appointment";
import type { InvoiceStatus } from "./invoice";

export interface SearchGroup<T> {
  /** Toplam eşleşme; items en fazla 5 kayıttır. */
  total: number;
  items: T[];
}

export interface SearchResponse {
  query: string;
  customers: SearchGroup<{ id: string; name: string; phone: string | null; email: string | null }>;
  appointments: SearchGroup<{
    id: string;
    customer_name: string;
    appointment_date: string;
    start_time: string;
    status: AppointmentStatus;
  }>;
  invoices: SearchGroup<{
    id: string;
    invoice_number: string;
    customer_name: string;
    status: InvoiceStatus;
    /** Çalışan/izleyici rolünde null (tutar gösterilmez). */
    total_amount: number | null;
  }>;
  products: SearchGroup<{ id: string; name: string; sku: string | null; current_stock: number }>;
}
