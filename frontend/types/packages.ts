export type PackageStatus = 'ACTIVE' | 'INACTIVE' | 'ARCHIVED';
export type CustomerPackageStatus = 'ACTIVE' | 'COMPLETED' | 'EXPIRED' | 'CANCELLED';
export type SessionStatus = 'PENDING' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW';
export type InstallmentStatus = 'PENDING' | 'PAID' | 'OVERDUE' | 'CANCELLED';

export interface ServicePackage {
  id: string;
  business_id: string;
  name: string;
  description: string | null;
  services: { service_id: string; service_name: string; session_count: number }[];
  total_sessions: number;
  price: number;
  discount_percentage: number;
  validity_days: number;
  is_installment_allowed: boolean;
  max_installments: number;
  status: PackageStatus;
  created_at: string;
  updated_at: string;
}

export interface CustomerPackage {
  id: string;
  business_id: string;
  customer_id: string;
  package_id: string;
  branch_id: string | null;
  purchased_at: string;
  expires_at: string | null;
  total_sessions: number;
  used_sessions: number;
  remaining_sessions: number;
  total_price: number;
  paid_amount: number;
  status: CustomerPackageStatus;
  notes: string | null;
  sessions?: PackageSession[];
  installments?: Installment[];
  customer_name?: string;
  package_name?: string;
}

export interface PackageSession {
  id: string;
  customer_package_id: string;
  service_id: string | null;
  appointment_id: string | null;
  session_number: number;
  session_date: string | null;
  status: SessionStatus;
  notes: string | null;
}

export interface Installment {
  id: string;
  customer_package_id: string;
  customer_id: string;
  installment_number: number;
  amount: number;
  due_date: string;
  paid_date: string | null;
  status: InstallmentStatus;
  payment_method: string | null;
  notes: string | null;
  customer_name?: string;
  package_name?: string;
}
