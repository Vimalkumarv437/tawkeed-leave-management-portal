import React from 'react';
import Table, { Column } from '../common/Table';
import Button from '../common/Button';
import { User } from '../../types/auth';

export interface UserTableProps {
  users?: User[];
  loading?: boolean;
  showActions?: boolean;
  onEdit?: (user: User) => void;
  onToggleStatus?: (user: User) => void;
}

export default function UserTable({
  users = [],
  loading = false,
  showActions = true,
  onEdit,
  onToggleStatus,
}: UserTableProps): React.ReactElement {
  const columns: Column<User>[] = [
    { header: 'ID', accessor: 'id' },
    {
      header: 'Name',
      render: (row) => `${row.first_name} ${row.last_name}`,
    },
    { header: 'Email', accessor: 'email' },
    {
      header: 'Role',
      render: (row) => <span className="role-tag">{row.role}</span>,
    },
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
  ];

  if (showActions && (onEdit || onToggleStatus)) {
    columns.push({
      header: 'Actions',
      render: (row) => (
        <div className="table-actions">
          {onEdit && (
            <Button variant="outline" size="sm" onClick={() => onEdit(row)}>
              Edit
            </Button>
          )}
          {onToggleStatus && (
            <Button
              variant={row.is_active ? 'danger' : 'success'}
              size="sm"
              onClick={() => onToggleStatus(row)}
            >
              {row.is_active ? 'Deactivate' : 'Reactivate'}
            </Button>
          )}
        </div>
      ),
    });
  }

  return <Table columns={columns} data={users} loading={loading} />;
}
