/**
 * Authentication Context
 * Sessions are securely backed by HttpOnly cookies.
 * JWT access tokens are never stored or accessed in JavaScript.
 */
import React, { createContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { authService } from '../services/authService';
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
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // If user is directly on public login routes, skip calling /auth/me on mount
    const publicPaths = ['/login', '/', '/change-password'];
    if (publicPaths.includes(window.location.pathname)) {
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
      setUser(null);
    }
  }, []);

  const login = async (credentials: LoginCredentials): Promise<User> => {
    // 1. Call Login API ONLY (backend sets HttpOnly cookie and returns id and role)
    const response = await authService.login(credentials);

    // 2. Construct safe authenticated session containing only id and role
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
    token: null, // JWT is never stored in client JS
    loading,
    isAuthenticated,
    role,
    login,
    logout,
    refreshUser: fetchCurrentUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};





