export interface AdminBusiness {
  id: string;
  name: string;
  slug: string;
  industry: string;
  email: string;
  phone: string;
  status: "ACTIVE" | "INACTIVE" | "SUSPENDED";
  plan: "FREE" | "PRO" | "ENTERPRISE";
  member_count: number;
  created_at: string;
  updated_at: string;
}
