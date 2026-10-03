export type CustomerStatus = "ACTIVE" | "INACTIVE";

export interface Customer {
  id: string;
  business_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  notes: string | null;
  status: CustomerStatus;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreatePayload {
  name: string;
  email?: string | null;
  phone?: string | null;
  notes?: string | null;
}

export interface CustomerUpdatePayload {
  name?: string;
  email?: string | null;
  phone?: string | null;
  notes?: string | null;
  status?: CustomerStatus;
}
