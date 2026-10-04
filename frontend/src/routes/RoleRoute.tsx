/**
 * RoleRoute Component
 */
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { getRoleDashboardPath, hasRequiredRole } from '../utils/roleUtils';
import Loading from '../components/common/Loading';
import { Role } from '../types';

interface RoleRouteProps {
  allowedRoles?: Role[];
}

export default function RoleRoute({ allowedRoles = [] }: RoleRouteProps) {
  const { role, loading, isAuthenticated } = useAuth();

  if (loading) {
    return <Loading fullScreen message="Checking permissions..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!hasRequiredRole(role, allowedRoles)) {
    return <Navigate to={getRoleDashboardPath(role)} replace />;
  }

  return <Outlet />;
}
