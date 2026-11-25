export interface DashboardStats {
  total_customers: number;
  total_appointments_today: number;
  total_appointments_this_month: number;
  /** null for roles without finance access (employee / viewer) */
  total_revenue_this_month: number | null;
  total_expenses_this_month: number | null;
  net_profit_this_month: number | null;
  pending_appointments: number;
  active_staff_count: number;
}

export interface RevenueDataPoint {
  period: string;
  income: number;
  expense: number;
  net: number;
  invoice_count: number;
}

export interface ServiceStats {
  name: string;
  booking_count: number;
  revenue: number | null;
  avg_rating: number | null;
}

export interface StaffPerformance {
  name: string;
  title: string | null;
  appointment_count: number;
  revenue: number | null;
  completion_rate: number;
}

export interface CustomerGrowthPoint {
  month: string;
  count: number;
}

export interface AppointmentReport {
  total_appointments: number;
  completed_count: number;
  cancelled_count: number;
  completion_rate: number;
  by_service: ServiceStats[];
}

export interface CustomerReport {
  new_customers_count: number;
  returning_customers_count: number;
  top_customers: { name: string; total_spent: number; visit_count: number }[];
  customer_growth: CustomerGrowthPoint[];
}

// ---------------------------------------------------------------- finance report (/reports/finance)

/** Gelir kaynakları ayrı: hiçbiri diğerini otomatik oluşturmuyor. Tutarlar TL. */
export interface FinanceAmounts {
  invoices: number;
  product_sales: number;
  installments: number;
  /** Gelir-Gider'e elle girilen gelir. */
  other_income: number;
  income: number;
  expense: number;
  net: number;
}

export interface FinancePeriod extends FinanceAmounts {
  /** Dönemin ilk yerel günü (YYYY-AA-GG): gün, hafta (pazartesi) ya da ay. */
  period: string;
}

export type FinanceGroup = "day" | "week" | "month";

export interface FinanceReport {
  start_date: string;
  end_date: string;
  group_by: FinanceGroup;
  series: FinancePeriod[];
  totals: FinanceAmounts;
  previous: FinanceAmounts & { start_date: string; end_date: string };
  expense_by_category: { name: string; color: string | null; amount: number; count: number }[];
  revenue_by_service: { name: string; amount: number; count: number }[];
  revenue_by_product: { name: string; amount: number; quantity: number }[];
}
