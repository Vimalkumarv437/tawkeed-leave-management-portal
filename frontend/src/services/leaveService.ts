/**
 * Leave Service (Employee / Manager leave actions)
 */
import api from './api';
import {
  LeaveRequest,
  CreateLeavePayload,
  CancelLeavePayload,
} from '../types';

export const leaveService = {
  /**
   * Create a new leave request
   */
  async createLeave(data: CreateLeavePayload): Promise<LeaveRequest> {
    const response = await api.post<LeaveRequest>('/leaves', data);
    return response.data;
  },

  /**
   * Get leave request details by ID
   */
  async getLeaveById(requestId: number): Promise<LeaveRequest> {
    const response = await api.get<LeaveRequest>(`/leaves/${requestId}`);
    return response.data;
  },

  /**
   * Cancel an employee's pending or approved leave request
   */
  async cancelLeave(requestId: number, data: CancelLeavePayload = {}): Promise<LeaveRequest> {
    const response = await api.post<LeaveRequest>(`/leaves/${requestId}/cancel`, data);
    return response.data;
  },
};
