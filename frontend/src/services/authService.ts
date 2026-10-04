/**
 * Authentication Service
 */
import api from './api';
import { LoginCredentials, TokenResponse, User } from '../types';

export const authService = {
  /**
   * Authenticate user with email and password
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/login', credentials);
    return response.data;
  },

  /**
   * Get current authenticated user profile
   */
  async getMe(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Logout user and clear httpOnly cookie
   */
  async logout(): Promise<void> {
    await api.post('/auth/logout');
  },
};

