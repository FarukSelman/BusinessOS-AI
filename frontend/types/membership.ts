export type MembershipRole = "OWNER" | "ADMIN" | "EMPLOYEE" | "VIEWER";

export interface Membership {
  id: string;
  role: MembershipRole;
  user: {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
  };
  business: {
    id: string;
    name: string;
    slug: string;
  };
  created_at: string;
  updated_at: string;
}
