export interface RegisterPayload {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  profile_image?: string | null;
}

export interface RegisterResponse {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  profile_image: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface MeResponse {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  profile_image: string | null;
  status: string;
  is_superadmin: boolean;
  /** False for accounts created with Google sign-in that never set a password. */
  has_password?: boolean;
}
