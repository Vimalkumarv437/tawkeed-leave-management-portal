import React, { useState, useEffect } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import BalanceManagement from '../../components/admin/BalanceManagement';
import ErrorMessage from '../../components/common/ErrorMessage';
import { useToast } from '../../context/ToastContext';
import { adminService } from '../../services/adminService';
import { extractErrorMessage } from '../../utils/errorUtils';
import { LeaveBalance, LeaveType, CreateBalancePayload, UpdateBalancePayload } from '../../types/leave';
import { User } from '../../types/auth';

export default function Balances(): React.ReactElement {
  const toast = useToast();
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  const fetchData = async (): Promise<void> => {
    setLoading(true);
    setError('');
    try {
      const [balancesRes, usersRes, typesRes] = await Promise.all([
        adminService.getBalances({ limit: 100 }),
        adminService.getUsers({ limit: 100 }),
        adminService.getLeaveTypes(),
      ]);
      setBalances(balancesRes.items || []);
      setUsers(Array.isArray(usersRes) ? usersRes : (usersRes as any).items || []);
      setLeaveTypes(typesRes.items || []);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async (payload: CreateBalancePayload): Promise<void> => {
    try {
      await adminService.createBalance(payload);
      toast.success('Leave balance allocated successfully.');
      fetchData();
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      setError(msg);
      toast.error(msg);
      throw err;
    }
  };

  const handleUpdate = async (balanceId: number, payload: UpdateBalancePayload): Promise<void> => {
    try {
      await adminService.updateBalance(balanceId, payload);
      toast.success('Leave balance adjusted successfully.');
      fetchData();
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      setError(msg);
      toast.error(msg);
      throw err;
    }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Leave Balance Administration"
        subtitle="Allocate and adjust employee annual leave allowances"
      />
      <ErrorMessage message={error} onDismiss={() => setError('')} />
      <BalanceManagement
        balances={balances}
        users={users}
        leaveTypes={leaveTypes}
        loading={loading}
        onCreateBalance={handleCreate}
        onUpdateBalance={handleUpdate}
      />
    </div>
  );
}
