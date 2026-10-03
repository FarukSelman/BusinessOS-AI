export interface Branch {
  id: string;
  business_id: string;
  name: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  is_main: boolean;
  is_active: boolean;
  working_hours: Record<string, { open: string; close: string }> | null;
  created_at: string;
  updated_at: string;
}

export type StaffStatus = 'ACTIVE' | 'INACTIVE' | 'ON_LEAVE';

export interface StaffProfile {
  id: string;
  business_id: string;
  branch_id: string | null;
  user_id: string | null;
  full_name: string;
  phone: string | null;
  email: string | null;
  title: string | null;
  bio: string | null;
  avatar_url: string | null;
  status: StaffStatus;
  color: string;
  services: { id: string; name: string }[];
  created_at: string;
  updated_at: string;
}

export interface StaffScheduleItem {
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_working: boolean;
}
