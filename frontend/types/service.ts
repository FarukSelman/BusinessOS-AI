export type ServiceStatus = "ACTIVE" | "INACTIVE";

export interface BusinessService {
  id: string;
  business_id: string;
  name: string;
  description: string | null;
  price: string;
  duration_minutes: number | null;
  category: string | null;
  status: ServiceStatus;
  created_at: string;
  updated_at: string;
}

export interface ServiceCreatePayload {
  name: string;
  description?: string | null;
  price: string | number;
  duration_minutes?: number | null;
  category?: string | null;
  status?: ServiceStatus;
}

export interface ServiceUpdatePayload {
  name?: string;
  description?: string | null;
  price?: string | number;
  duration_minutes?: number | null;
  category?: string | null;
  status?: ServiceStatus;
}
