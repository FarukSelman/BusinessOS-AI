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
