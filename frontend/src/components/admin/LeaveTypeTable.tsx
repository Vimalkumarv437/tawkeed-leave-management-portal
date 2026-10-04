import React from 'react';
import Table, { Column } from '../common/Table';
import Button from '../common/Button';
import { LeaveType } from '../../types/leave';

export interface LeaveTypeTableProps {
  leaveTypes?: LeaveType[];
  loading?: boolean;
  onEdit?: (leaveType: LeaveType) => void;
  onDelete?: (leaveType: LeaveType) => void;
}

export default function LeaveTypeTable({
  leaveTypes = [],
  loading = false,
  onEdit,
  onDelete,
}: LeaveTypeTableProps): React.ReactElement {
  const columns: Column<LeaveType>[] = [
    { header: 'ID', accessor: 'id' },
    { header: 'Name', accessor: 'name' },
    { header: 'Code', accessor: 'code' },
    { header: 'Allowance (Days)', accessor: 'default_annual_allowance' },
    {
      header: 'Status',
      render: (row) => (
        <span
          className={`badge ${row.is_active ? 'badge-success' : 'badge-muted'}`}
        >
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      header: 'Actions',
      render: (row) => (
        <div className="table-actions">
          {onEdit && (
            <Button variant="outline" size="sm" onClick={() => onEdit(row)}>
              Edit
            </Button>
          )}
          {onDelete && (
            <Button variant="danger" size="sm" onClick={() => onDelete(row)}>
              Delete
            </Button>
          )}
        </div>
      ),
    },
  ];

  return <Table columns={columns} data={leaveTypes} loading={loading} />;
}
