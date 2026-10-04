/**
 * Admin Service (User, leave type, balance, holiday, and audit log management)
 */
import api from './api';
import {
  User,
  UserCreatePayload,
  UserUpdatePayload,
  LeaveType,
  LeaveBalance,
  CreateBalancePayload,
  UpdateBalancePayload,
  PublicHoliday,
  AuditLog,
  PaginatedResponse,
} from '../types';

export const adminService = {
  // --- USERS ---
  async getUsers(params: Record<string, any> = {}): Promise<User[]> {
    const response = await api.get<User[]>('/admin/users', { params });
    return response.data;
  },
  async getUserById(userId: number): Promise<User> {
    const response = await api.get<User>(`/admin/users/${userId}`);
    return response.data;
  },
  async createUser(data: UserCreatePayload): Promise<User> {
    const response = await api.post<User>('/admin/users', data);
    return response.data;
  },
  async updateUser(userId: number, data: UserUpdatePayload): Promise<User> {
    const response = await api.patch<User>(`/admin/users/${userId}`, data);
    return response.data;
  },
  async deactivateUser(userId: number): Promise<User> {
    const response = await api.post<User>(`/admin/users/${userId}/deactivate`);
    return response.data;
  },
  async reactivateUser(userId: number): Promise<User> {
    const response = await api.post<User>(`/admin/users/${userId}/reactivate`);
    return response.data;
  },

  // --- LEAVE TYPES ---
  async getLeaveTypes(params: Record<string, any> = {}): Promise<PaginatedResponse<LeaveType>> {
    const response = await api.get<PaginatedResponse<LeaveType>>('/admin/leave-types', { params });
    return response.data;
  },
  async createLeaveType(data: Partial<LeaveType>): Promise<LeaveType> {
    const response = await api.post<LeaveType>('/admin/leave-types', data);
    return response.data;
  },
  async updateLeaveType(leaveTypeId: number, data: Partial<LeaveType>): Promise<LeaveType> {
    const response = await api.patch<LeaveType>(`/admin/leave-types/${leaveTypeId}`, data);
    return response.data;
  },
  async deleteLeaveType(leaveTypeId: number): Promise<void> {
    await api.delete(`/admin/leave-types/${leaveTypeId}`);
  },

  // --- BALANCES ---
  async getBalances(params: Record<string, any> = {}): Promise<PaginatedResponse<LeaveBalance>> {
    const response = await api.get<PaginatedResponse<LeaveBalance>>('/admin/balances', { params });
    return response.data;
  },
  async createBalance(data: CreateBalancePayload): Promise<LeaveBalance> {
    const response = await api.post<LeaveBalance>('/admin/balances', data);
    return response.data;
  },
  async updateBalance(balanceId: number, data: UpdateBalancePayload): Promise<LeaveBalance> {
    const response = await api.patch<LeaveBalance>(`/admin/balances/${balanceId}`, data);
    return response.data;
  },

  // --- PUBLIC HOLIDAYS ---
  async getHolidays(params: Record<string, any> = {}): Promise<PaginatedResponse<PublicHoliday>> {
    const response = await api.get<PaginatedResponse<PublicHoliday>>('/admin/holidays', { params });
    return response.data;
  },
  async createHoliday(data: Partial<PublicHoliday>): Promise<PublicHoliday> {
    const response = await api.post<PublicHoliday>('/admin/holidays', data);
    return response.data;
  },
  async updateHoliday(holidayId: number, data: Partial<PublicHoliday>): Promise<PublicHoliday> {
    const response = await api.patch<PublicHoliday>(`/admin/holidays/${holidayId}`, data);
    return response.data;
  },
  async deleteHoliday(holidayId: number): Promise<void> {
    await api.delete(`/admin/holidays/${holidayId}`);
  },

  // --- AUDIT LOGS ---
  async getAuditLogs(params: Record<string, any> = {}): Promise<PaginatedResponse<AuditLog>> {
    const response = await api.get<PaginatedResponse<AuditLog>>('/admin/audit-logs', { params });
    return response.data;
  },
};
