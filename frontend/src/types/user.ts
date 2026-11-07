export type UserRole = "citizen" | "officer" | "admin";

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  phone?: string;
  role: UserRole;
  city?: string;
  ward?: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  phone?: string;
  city?: string;
  ward?: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: "bearer";
  expires_in?: number;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}
