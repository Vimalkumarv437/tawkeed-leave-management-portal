/**
 * Leave and Balance Types
 */
import { User } from './auth';

export type LeaveStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
export type HalfDayType = 'NONE' | 'FIRST_HALF' | 'SECOND_HALF';

export interface LeaveType {
  id: number;
  name: string;
  code: string;
  description?: string | null;
  default_annual_allowance: number | string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface LeaveRequestAllocation {
  id: number;
  leave_request_id: number;
  year: number;
  allocated_days: number | string;
  created_at?: string;
}

export interface LeaveRequest {
  id: number;
  user_id: number;
  leave_type_id: number;
  start_date: string;
  end_date: string;
  start_half_day: HalfDayType;
  end_half_day: HalfDayType;
  total_days: number | string;
  reason?: string | null;
  status: LeaveStatus;
  approved_by_id?: number | null;
  approval_comment?: string | null;
  approved_at?: string | null;
  cancelled_by_id?: number | null;
  cancellation_reason?: string | null;
  cancelled_at?: string | null;
  created_at: string;
  updated_at?: string;
  user?: User;
  leave_type?: LeaveType;
  allocations?: LeaveRequestAllocation[];
}

export interface LeaveBalance {
  id: number;
  user_id: number;
  leave_type_id: number;
  year: number;
  allocated_days: number | string;
  used_days: number | string;
  reserved_days: number | string;
  remaining_days?: number | string;
  user?: User;
  leave_type?: LeaveType;
}

export interface CreateLeavePayload {
  leave_type_id: number;
  start_date: string;
  end_date: string;
  start_half_day?: HalfDayType;
  end_half_day?: HalfDayType;
  reason?: string;
}

export interface LeaveDecisionPayload {
  comment?: string;
}

export interface CancelLeavePayload {
  reason?: string;
}

export interface CreateBalancePayload {
  user_id: number;
  leave_type_id: number;
  year: number;
  allocated_days: number;
}

export interface UpdateBalancePayload {
  allocated_days: number;
}

