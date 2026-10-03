export type AppointmentStatus = "PENDING" | "CONFIRMED" | "CANCELLED" | "COMPLETED" | "NO_SHOW";

export interface Appointment {
  id: string;
  business_id: string;
  customer_name: string;
  customer_phone: string | null;
  customer_email: string | null;
  service_id: string | null;
  customer_id: string | null;
  appointment_date: string; // YYYY-MM-DD
  start_time: string; // HH:MM:SS
  end_time: string | null;
  status: AppointmentStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppointmentCreatePayload {
  customer_name: string;
  customer_phone?: string | null;
  customer_email?: string | null;
  service_id?: string | null;
  customer_id?: string | null;
  appointment_date: string;
  start_time: string;
  end_time?: string | null;
  notes?: string | null;
}

export interface AppointmentUpdatePayload {
  customer_name?: string;
  customer_phone?: string | null;
  customer_email?: string | null;
  service_id?: string | null;
  customer_id?: string | null;
  appointment_date?: string;
  start_time?: string;
  end_time?: string | null;
  status?: AppointmentStatus;
  notes?: string | null;
}

export interface AvailableSlotsResponse {
  date: string;
  available_slots: string[];
}
