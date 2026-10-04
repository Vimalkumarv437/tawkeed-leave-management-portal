/**
 * Admin, Holiday, and Audit Log Types
 */
import { User } from './auth';

export type AuditAction =
  | 'CREATE_LEAVE'
  | 'APPROVE_LEAVE'
  | 'REJECT_LEAVE'
  | 'CANCEL_LEAVE'
  | 'CREATE_USER'
  | 'UPDATE_USER'
  | 'DEACTIVATE_USER'
  | 'CREATE_LEAVE_TYPE'
  | 'UPDATE_LEAVE_TYPE'
  | 'CREATE_HOLIDAY'
  | 'UPDATE_HOLIDAY';

export interface PublicHoliday {
  id: number;
  holiday_date: string;
  name: string;
  description?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface AuditLog {
  id: number;
  user_id?: number | null;
  action: AuditAction;
  entity_type: string;
  entity_id: number;
  details?: Record<string, any> | null;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
  user?: User | null;
}
