/**
 * Role Utilities
 */
import { Role } from '../types';
import { ROLES } from './constants';

export function getRoleDashboardPath(role?: Role | null): string {
  switch (role) {
    case ROLES.ADMIN:
      return '/admin';
    case ROLES.MANAGER:
      return '/manager';
    case ROLES.EMPLOYEE:
      return '/employee';
    default:
      return '/login';
  }
}

export function hasRequiredRole(userRole?: Role | null, allowedRoles: Role[] = []): boolean {
  if (!userRole) return false;
  if (!allowedRoles || allowedRoles.length === 0) return true;
  return allowedRoles.includes(userRole);
}
