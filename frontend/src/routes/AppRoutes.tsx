/**
 * Application Routes Definition
 */
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import RoleRoute from './RoleRoute';
import { ROLES } from '../utils/constants';

// Layout
import DashboardLayout from '../components/layout/DashboardLayout';

// Auth Pages
import Login from '../pages/auth/Login';
import ChangePassword from '../pages/auth/ChangePassword';

// Employee Pages
import EmployeeDashboard from '../pages/employee/EmployeeDashboard';
import MyLeaves from '../pages/employee/MyLeaves';
import ApplyLeave from '../pages/employee/ApplyLeave';
import EmployeeLeaveDetails from '../pages/employee/LeaveDetails';
import MyBalance from '../pages/employee/MyBalance';

// Manager Pages
import ManagerDashboard from '../pages/manager/ManagerDashboard';
import TeamRequests from '../pages/manager/TeamRequests';
import TeamCalendar from '../pages/manager/TeamCalendar';
import RequestDetails from '../pages/manager/RequestDetails';

// Admin Pages
import AdminDashboard from '../pages/admin/AdminDashboard';
import Users from '../pages/admin/Users';
import LeaveTypes from '../pages/admin/LeaveTypes';
import Balances from '../pages/admin/Balances';
import Holidays from '../pages/admin/Holidays';
import AuditLogs from '../pages/admin/AuditLogs';

// NotFound
import NotFound from '../pages/NotFound';

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/change-password" element={<ChangePassword />} />

      {/* Authenticated Root Redirection */}
      <Route element={<ProtectedRoute />}>
        {/* EMPLOYEE ROUTES */}
        <Route element={<RoleRoute allowedRoles={[ROLES.EMPLOYEE]} />}>
          <Route element={<DashboardLayout />}>
            <Route path="/employee" element={<EmployeeDashboard />} />
            <Route path="/employee/leaves" element={<MyLeaves />} />
            <Route path="/employee/leaves/apply" element={<ApplyLeave />} />
            <Route path="/employee/apply-leave" element={<Navigate to="/employee/leaves/apply" replace />} />
            <Route path="/employee/leaves/:id" element={<EmployeeLeaveDetails />} />
            <Route path="/employee/balance" element={<MyBalance />} />
          </Route>
        </Route>

        {/* MANAGER ROUTES */}
        <Route element={<RoleRoute allowedRoles={[ROLES.MANAGER]} />}>
          <Route element={<DashboardLayout />}>
            <Route path="/manager" element={<ManagerDashboard />} />
            <Route path="/manager/requests" element={<TeamRequests />} />
            <Route path="/manager/requests/:id" element={<RequestDetails />} />
            <Route path="/manager/calendar" element={<TeamCalendar />} />
            {/* Manager employee-self features */}
            <Route path="/manager/leaves" element={<MyLeaves />} />
            <Route path="/manager/leaves/apply" element={<ApplyLeave />} />
            <Route path="/manager/balance" element={<MyBalance />} />
          </Route>
        </Route>

        {/* ADMIN ROUTES */}
        <Route element={<RoleRoute allowedRoles={[ROLES.ADMIN]} />}>
          <Route element={<DashboardLayout />}>
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/users" element={<Users />} />
            <Route path="/admin/leave-types" element={<LeaveTypes />} />
            <Route path="/admin/balances" element={<Balances />} />
            <Route path="/admin/holidays" element={<Holidays />} />
            <Route path="/admin/audit-logs" element={<AuditLogs />} />
          </Route>
        </Route>
      </Route>

      {/* Root redirect */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* 404 Pages */}
      <Route path="/not-found" element={<NotFound />} />
      <Route path="*" element={<Navigate to="/not-found" replace />} />
    </Routes>
  );
}
