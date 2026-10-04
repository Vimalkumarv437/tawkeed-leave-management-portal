/**
 * Application Constants
 */
import { Role, LeaveStatus, HalfDayType, AuditAction } from '../types';

export const ROLES: Record<string, Role> = {
  ADMIN: 'ADMIN',
  MANAGER: 'MANAGER',
  EMPLOYEE: 'EMPLOYEE',
};

export const LEAVE_STATUS: Record<string, LeaveStatus> = {
  PENDING: 'PENDING',
  APPROVED: 'APPROVED',
  REJECTED: 'REJECTED',
  CANCELLED: 'CANCELLED',
};

export const HALF_DAY_TYPE: Record<string, HalfDayType> = {
  NONE: 'NONE',
  FIRST_HALF: 'FIRST_HALF',
  SECOND_HALF: 'SECOND_HALF',
};

export const AUDIT_ACTIONS: Record<string, AuditAction> = {
  CREATE_LEAVE: 'CREATE_LEAVE',
  APPROVE_LEAVE: 'APPROVE_LEAVE',
  REJECT_LEAVE: 'REJECT_LEAVE',
  CANCEL_LEAVE: 'CANCEL_LEAVE',
  CREATE_USER: 'CREATE_USER',
  UPDATE_USER: 'UPDATE_USER',
  DEACTIVATE_USER: 'DEACTIVATE_USER',
  CREATE_LEAVE_TYPE: 'CREATE_LEAVE_TYPE',
  UPDATE_LEAVE_TYPE: 'UPDATE_LEAVE_TYPE',
  CREATE_HOLIDAY: 'CREATE_HOLIDAY',
  UPDATE_HOLIDAY: 'UPDATE_HOLIDAY',
};

export const STORAGE_KEYS = {
  TOKEN: 'tawkeed_access_token',
  USER: 'tawkeed_user_profile',
} as const;
