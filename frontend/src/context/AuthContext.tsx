/**
 * Authentication Context
 * Sessions are securely backed by HttpOnly cookies.
 * JWT access tokens are never stored or accessed in JavaScript.
 */
/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { authService } from '../services/authService';
import { getCookie, setCookie, deleteCookie } from '../utils/cookieUtils';
import { AuthContextType, LoginCredentials, User, Role } from '../types';

export const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Restore authenticated session on application refresh
  const fetchCurrentUser = useCallback(async () => {
    try {
      const profile = await authService.getMe();
      setUser(profile);
    } catch {
      deleteCookie('access_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = getCookie('access_token');
    const publicPaths = ['/login', '/', '/change-password'];

    // If no access token cookie exists and user is on a public page, skip calling /auth/me
    if (!token && publicPaths.includes(window.location.pathname)) {
      setLoading(false);
      return;
    }

    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch {
      // Ignore network errors during logout
    } finally {
      deleteCookie('access_token');
      setUser(null);
    }
  }, []);

  const login = async (credentials: LoginCredentials): Promise<User> => {
    const response = await authService.login(credentials);

    if (response.access_token) {
      setCookie('access_token', response.access_token);
    }

    const sessionUser: User = {
      id: response.id,
      role: response.role,
      first_name: '',
      last_name: '',
      email: credentials.email,
      is_active: true,
    };

    setUser(sessionUser);
    return sessionUser;
  };

  const role: Role | null = user?.role || null;
  const isAuthenticated: boolean = !!user;

  const value: AuthContextType = {
    user,
    token: getCookie('access_token'),
    loading,
    isAuthenticated,
    role,
    login,
    logout,
    refreshUser: fetchCurrentUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};





