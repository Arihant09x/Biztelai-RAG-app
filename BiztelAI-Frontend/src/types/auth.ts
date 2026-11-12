export type UserRole = "admin" | "supervisor" | "operator" | "auditor";

export interface User {
  id: string;
  email: string;
  full_name: string;
  department?: string;
  role: UserRole;
  is_active: boolean;
  is_supervisor?: boolean;
  is_admin?: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in?: number;
}

export interface LoginResponse {
  tokens: AuthTokens;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  department?: string;
  role?: UserRole;
}

export interface LoginRequest {
  email: string;
  password: string;
}
