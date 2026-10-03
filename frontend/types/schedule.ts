export type BlockType = 'FULL_DAY' | 'TIME_RANGE' | 'RECURRING';
export type RecurrenceDay = 'MONDAY' | 'TUESDAY' | 'WEDNESDAY' | 'THURSDAY' | 'FRIDAY' | 'SATURDAY' | 'SUNDAY';

export interface ScheduleBlock {
  id: string;
  business_id: string;
  branch_id: string | null;
  block_type: BlockType;
  title: string | null;
  start_date: string | null;
  end_date: string | null;
  start_time: string | null;
  end_time: string | null;
  recurrence_day: RecurrenceDay | null;
  reason: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// 0 = Monday ... 6 = Sunday (same as backend / Python weekday())
export interface BusinessHoursItem {
  day_of_week: number;
  open_time: string | null;
  close_time: string | null;
  is_closed: boolean;
}

export interface BusinessHours extends BusinessHoursItem {
  id: string;
  business_id: string;
  branch_id: string | null;
}

export interface OpenWindow {
  date: string;
  branch_id: string | null;
  is_open: boolean;
  open_time: string | null;
  close_time: string | null;
}

export interface ReminderChannel { EMAIL: 'EMAIL'; SMS: 'SMS'; }
export type ReminderChannelType = 'EMAIL' | 'SMS';
export type ReminderStatusType = 'PENDING' | 'SENT' | 'FAILED' | 'SKIPPED';

export interface ReminderConfig {
  id: string;
  business_id: string;
  channel: ReminderChannelType;
  hours_before: number;
  message_template: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReminderLog {
  id: string;
  business_id: string;
  appointment_id: string;
  reminder_config_id: string;
  channel: ReminderChannelType;
  appointment_start: string;
  recipient_email: string | null;
  attempts: number;
  sent_at: string | null;
  status: ReminderStatusType;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  customer_name: string | null;
  hours_before: number | null;
}

export interface TestReminderResult {
  status: string;
  recipient: string;
}
