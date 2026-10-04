/**
 * Authentication and User Types
 */

export type Role = 'ADMIN' | 'MANAGER' | 'EMPLOYEE';

export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  role: Role;
  is_active: boolean;
  manager_id?: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface LoginCredentials {
  email: string;
  password?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  id: number;
  role: Role;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  role: Role | null;
  login: (credentials: LoginCredentials) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export interface UserCreatePayload {
  first_name: string;
  last_name: string;
  email: string;
  password?: string;
  role: Role;
  manager_id?: number | null;
}

export interface UserUpdatePayload {
  first_name?: string;
  last_name?: string;
  email?: string;
  role?: Role;
  manager_id?: number | null;
  is_active?: boolean;
}

