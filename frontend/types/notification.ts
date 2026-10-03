export type NotificationType = 'APPOINTMENT_CREATED' | 'APPOINTMENT_CANCELLED' | 'APPOINTMENT_COMPLETED' | 'DOCUMENT_READY' | 'DOCUMENT_FAILED' | 'INVOICE_CREATED' | 'INVOICE_PAID' | 'TEAM_INVITATION' | 'SYSTEM';

export interface AppNotification {
  id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  reference_id: string | null;
  reference_type: string | null;
  created_at: string;
}

export interface UnreadCountResponse {
  count: number;
}
