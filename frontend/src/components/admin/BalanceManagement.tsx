import React, { useState } from 'react';
import Table, { Column } from '../common/Table';
import Button from '../common/Button';
import Modal from '../common/Modal';
import Input from '../common/Input';
import Select from '../common/Select';
import ErrorMessage from '../common/ErrorMessage';
import { LeaveBalance, LeaveType, CreateBalancePayload, UpdateBalancePayload } from '../../types/leave';
import { User } from '../../types/auth';

export interface BalanceManagementProps {
  balances?: LeaveBalance[];
  users?: User[];
  leaveTypes?: LeaveType[];
  loading?: boolean;
  onCreateBalance: (payload: CreateBalancePayload) => Promise<void>;
  onUpdateBalance: (balanceId: number, payload: UpdateBalancePayload) => Promise<void>;
}

export default function BalanceManagement({
  balances = [],
  users = [],
  leaveTypes = [],
  loading = false,
  onCreateBalance,
  onUpdateBalance,
}: BalanceManagementProps): React.ReactElement {
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingBalance, setEditingBalance] = useState<LeaveBalance | null>(null);
  const [formData, setFormData] = useState<{
    user_id: string;
    leave_type_id: string;
    year: number;
    allocated_days: string;
  }>({
    user_id: '',
    leave_type_id: '',
    year: new Date().getFullYear(),
    allocated_days: '',
  });
  const [error, setError] = useState<string>('');

  const openCreateModal = (): void => {
    setEditingBalance(null);
    setFormData({
      user_id: '',
      leave_type_id: '',
      year: new Date().getFullYear(),
      allocated_days: '',
    });
    setError('');
    setIsModalOpen(true);
  };

  const openEditModal = (balance: LeaveBalance): void => {
    setEditingBalance(balance);
    setFormData({
      user_id: String(balance.user_id),
      leave_type_id: String(balance.leave_type_id),
      year: balance.year,
      allocated_days: String(balance.allocated_days),
    });
    setError('');
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    try {
      if (editingBalance) {
        await onUpdateBalance(editingBalance.id, {
          allocated_days: parseFloat(formData.allocated_days),
        });
      } else {
        const userIdNum = parseInt(formData.user_id, 10);
        const leaveTypeIdNum = parseInt(formData.leave_type_id, 10);
        const yearNum = Number(formData.year);
        const allocatedDaysNum = parseFloat(formData.allocated_days);

        // Check if a balance already exists locally
        const existing = balances.find(
          (b) => b.user_id === userIdNum && b.leave_type_id === leaveTypeIdNum && b.year === yearNum
        );

        if (existing) {
          // Gracefully adjust the existing balance
          await onUpdateBalance(existing.id, {
            allocated_days: allocatedDaysNum,
          });
        } else {
          await onCreateBalance({
            user_id: userIdNum,
            leave_type_id: leaveTypeIdNum,
            year: yearNum,
            allocated_days: allocatedDaysNum,
          });
        }
      }
      setIsModalOpen(false);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Operation failed';
      setError(msg);
    }
  };

  const columns: Column<LeaveBalance>[] = [
    { header: 'ID', accessor: 'id' },
    {
      header: 'Employee',
      render: (row) => {
        const u = users.find((user) => user.id === row.user_id);
        if (u) {
          return `${u.first_name} ${u.last_name}`;
        }
        return row.user ? `${row.user.first_name} ${row.user.last_name}` : `User #${row.user_id}`;
      },
    },
    {
      header: 'Leave Type',
      render: (row) => {
        const lt = leaveTypes.find((type) => type.id === row.leave_type_id);
        if (lt) {
          return `${lt.name} (${lt.code})`;
        }
        return row.leave_type?.name || `Type #${row.leave_type_id}`;
      },
    },
    { header: 'Year', accessor: 'year' },
    { header: 'Allocated', accessor: 'allocated_days' },
    { header: 'Used', accessor: 'used_days' },
    { header: 'Reserved', accessor: 'reserved_days' },
    {
      header: 'Actions',
      render: (row) => (
        <Button variant="outline" size="sm" onClick={() => openEditModal(row)}>
          Adjust
        </Button>
      ),
    },
  ];

  return (
    <div className="balance-management-container">
      <div className="table-top-bar">
        <Button variant="primary" onClick={openCreateModal}>
          + Allocate Balance
        </Button>
      </div>
      <Table columns={columns} data={balances} loading={loading} />

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingBalance ? 'Adjust Leave Balance' : 'Allocate Leave Balance'}
        size="sm"
      >
        <form onSubmit={handleSubmit}>
          <ErrorMessage message={error} />
          {!editingBalance && (
            <>
              <Select
                label="Employee"
                value={formData.user_id}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, user_id: e.target.value }))
                }
                options={users.map((u) => ({
                  value: u.id,
                  label: `${u.first_name} ${u.last_name} (${u.email})`,
                }))}
                required
              />
              <Select
                label="Leave Type"
                value={formData.leave_type_id}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    leave_type_id: e.target.value,
                  }))
                }
                options={leaveTypes.map((lt) => ({
                  value: lt.id,
                  label: lt.name,
                }))}
                required
              />
              <Input
                label="Year"
                name="year"
                type="number"
                min="2000"
                max="2100"
                value={formData.year}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, year: Number(e.target.value) }))
                }
                required
              />
            </>
          )}
          <Input
            label="Allocated Days"
            name="allocated_days"
            type="number"
            step="0.5"
            min="0"
            value={formData.allocated_days}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                allocated_days: e.target.value,
              }))
            }
            required
          />
          <div className="form-actions">
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Save
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
