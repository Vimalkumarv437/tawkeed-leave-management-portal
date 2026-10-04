import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/layout/PageHeader';
import Button from '../../components/common/Button';
import BalanceCard from '../../components/balance/BalanceCard';
import UserTable from '../../components/admin/UserTable';
import Loading from '../../components/common/Loading';
import ErrorMessage from '../../components/common/ErrorMessage';
import { IconUsers, IconBriefcase, IconTags } from '../../components/common/Icons';
import { adminService } from '../../services/adminService';
import { ROLES } from '../../utils/constants';
import { extractErrorMessage } from '../../utils/errorUtils';
import { User } from '../../types/auth';
import { LeaveType } from '../../types/leave';

export default function AdminDashboard(): React.ReactElement {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    async function loadAdminData(): Promise<void> {
      try {
        const [usersRes, leaveTypesRes] = await Promise.all([
          adminService.getUsers({ offset: 0, limit: 100 }),
          adminService.getLeaveTypes(),
        ]);
        const usersList = (usersRes as any).items || (Array.isArray(usersRes) ? usersRes : []);
        const leaveTypesList = (leaveTypesRes as any).items || (Array.isArray(leaveTypesRes) ? leaveTypesRes : []);
        setUsers(usersList);
        setLeaveTypes(leaveTypesList);
      } catch (err: unknown) {
        setError(extractErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    loadAdminData();
  }, []);

  const totalEmployees = users.filter((u) => u.role === ROLES.EMPLOYEE).length;
  const totalManagers = users.filter((u) => u.role === ROLES.MANAGER).length;

  if (loading) return <Loading message="Loading admin dashboard..." />;

  return (
    <div className="dashboard-container">
      <PageHeader
        title="Admin Dashboard"
        subtitle="System overview, user administration, and policy management"
        action={
          <Button variant="primary" onClick={() => navigate('/admin/users')}>
            <IconUsers size={16} className="mr-1" />
            <span>Manage Users</span>
          </Button>
        }
      />
      <ErrorMessage message={error} />
      <div className="stats-grid">
        <BalanceCard
          title="Total Users"
          remaining={users.length}
          allocated={users.length}
          used={0}
          reserved={0}
          icon={<IconUsers size={18} className="text-blue-600" />}
        />
        <BalanceCard
          title="Employees"
          remaining={totalEmployees}
          allocated={totalEmployees}
          used={0}
          reserved={0}
          icon={<IconBriefcase size={18} className="text-emerald-600" />}
        />
        <BalanceCard
          title="Managers"
          remaining={totalManagers}
          allocated={totalManagers}
          used={0}
          reserved={0}
          icon={<IconUsers size={18} className="text-indigo-600" />}
        />
        <BalanceCard
          title="Leave Types"
          remaining={leaveTypes.length}
          allocated={leaveTypes.length}
          used={0}
          reserved={0}
          icon={<IconTags size={18} className="text-amber-600" />}
        />
      </div>

      <div className="dashboard-section mt-6">
        <div className="section-header flex justify-between items-center mb-3">
          <h3>Recent Users</h3>
          <Button variant="outline" size="sm" onClick={() => navigate('/admin/users')}>
            View All Users
          </Button>
        </div>
        <UserTable users={users.slice(0, 5)} showActions={false} />
      </div>
    </div>
  );
}
