/**
 * Employee Service (Self balance & leave history)
 */
import api from './api';
import { LeaveBalance, LeaveRequest, PaginatedResponse } from '../types';

export const employeeService = {
  /**
   * Get authenticated user's leave balances for a year
   */
  async getMyBalances(year: number, offset: number = 0, limit: number = 50): Promise<PaginatedResponse<LeaveBalance>> {
    const response = await api.get<PaginatedResponse<LeaveBalance>>('/employees/me/balances', {
      params: { year, offset, limit },
    });
    return response.data;
  },

  /**
   * Get authenticated user's leave request history
   */
  async getMyLeaves(offset: number = 0, limit: number = 50): Promise<PaginatedResponse<LeaveRequest>> {
    const response = await api.get<PaginatedResponse<LeaveRequest>>('/employees/me/leaves', {
      params: { offset, limit },
    });
    return response.data;
  },
};
