export interface Business {
  id: string;
  name: string;
  slug: string;
  industry: string;
  email: string;
  phone: string;
  website: string | null;
  logo_url: string | null;
  status: string;
  /** Online booking page: confirm bookings automatically instead of PENDING. */
  online_booking_auto_confirm?: boolean;
  created_at: string;
  updated_at: string;
}

export interface BusinessCreatePayload {
  name: string;
  industry: string;
  email: string;
  phone: string;
  website?: string | null;
  logo_url?: string | null;
}
