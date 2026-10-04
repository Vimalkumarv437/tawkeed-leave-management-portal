/**
 * Manager Service (Team leave management & approvals)
 */
import api from './api';
import {
  LeaveRequest,
  LeaveDecisionPayload,
  PaginatedResponse,
} from '../types';

export const managerService = {
  /**
   * Get leave requests belonging to the manager's team
   */
  async getTeamRequests(params: Record<string, unknown> = {}): Promise<PaginatedResponse<LeaveRequest>> {
    const response = await api.get<PaginatedResponse<LeaveRequest>>('/manager/requests', { params });
    return response.data;
  },

  /**
   * Approve a pending team leave request
   */
  async approveRequest(requestId: number, data: LeaveDecisionPayload = {}): Promise<LeaveRequest> {
    const response = await api.post<LeaveRequest>(`/manager/requests/${requestId}/approve`, data);
    return response.data;
  },

  /**
   * Reject a pending team leave request
   */
  async rejectRequest(requestId: number, data: LeaveDecisionPayload = {}): Promise<LeaveRequest> {
    const response = await api.post<LeaveRequest>(`/manager/requests/${requestId}/reject`, data);
    return response.data;
  },

  /**
   * Get team calendar (approved team leaves)
   */
  async getTeamCalendar(params: Record<string, unknown> = {}): Promise<PaginatedResponse<LeaveRequest>> {
    const response = await api.get<PaginatedResponse<LeaveRequest>>('/manager/calendar', { params });
    return response.data;
  },
};
