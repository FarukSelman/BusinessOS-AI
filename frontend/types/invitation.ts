import { MembershipRole } from './membership';

export type InvitationStatus = "PENDING" | "ACCEPTED" | "DECLINED" | "CANCELLED" | "EXPIRED";

export interface Invitation {
  id: string;
  business_id: string;
  email: string;
  token: string;
  role: MembershipRole;
  status: InvitationStatus;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
  updated_at: string;
  business: {
    id: string;
    name: string;
    slug: string;
  };
}

export interface InvitationCreatePayload {
  email: string;
  role?: MembershipRole;
}
