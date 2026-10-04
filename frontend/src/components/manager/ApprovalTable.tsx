import React from 'react';
import Table, { Column } from '../common/Table';
import LeaveStatusBadge from '../leave/LeaveStatusBadge';
import Button from '../common/Button';
import { formatDate } from '../../utils/dateUtils';
import { LEAVE_STATUS } from '../../utils/constants';
import { LeaveRequest } from '../../types/leave';
import { IconCheck, IconX, IconEye } from '../common/Icons';

export interface ApprovalTableProps {
  requests?: LeaveRequest[];
  loading?: boolean;
  onApprove?: (request: LeaveRequest) => void;
  onReject?: (request: LeaveRequest) => void;
  onViewDetails?: (request: LeaveRequest) => void;
  emptyMessage?: string;
}

export default function ApprovalTable({
  requests = [],
  loading = false,
  onApprove,
  onReject,
  onViewDetails,
  emptyMessage = 'No leave requests found.',
}: ApprovalTableProps): React.ReactElement {
  const getInitials = (firstName?: string, lastName?: string): string => {
    const f = firstName?.[0] || '';
    const l = lastName?.[0] || '';
    return (f + l).toUpperCase() || 'U';
  };

  const columns: Column<LeaveRequest>[] = [
    {
      header: 'Employee',
      render: (row) => {
        const name = row.user
          ? `${row.user.first_name} ${row.user.last_name}`
          : `Employee #${row.user_id}`;
        const email = row.user?.email || '';
        const initials = getInitials(row.user?.first_name, row.user?.last_name);

        return (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-bold shrink-0 border border-slate-200">
              {initials}
            </div>
            <div className="flex flex-col min-w-0">
              <span className="font-semibold text-slate-900 text-xs sm:text-sm truncate">{name}</span>
              {email && <span className="text-[11px] text-slate-500 truncate">{email}</span>}
            </div>
          </div>
        );
      },
    },
    {
      header: 'Leave Type',
      render: (row) => (
        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200/70">
          {row.leave_type?.name || `Type #${row.leave_type_id}`}
        </span>
      ),
    },
    {
      header: 'Dates',
      render: (row) => (
        <div className="flex flex-col text-xs text-slate-700 font-medium">
          <span>{formatDate(row.start_date)}</span>
          <span className="text-slate-400 text-[10px]">to {formatDate(row.end_date)}</span>
        </div>
      ),
    },
    {
      header: 'Days',
      render: (row) => (
        <span className="text-xs font-semibold text-slate-800">
          {row.total_days} {Number(row.total_days) === 1 ? 'day' : 'days'}
        </span>
      ),
    },
    {
      header: 'Reason',
      render: (row) => (
        <span className="text-xs text-slate-600 max-w-[180px] truncate block" title={row.reason || ''}>
          {row.reason ? row.reason : <span className="text-slate-400 italic">No reason provided</span>}
        </span>
      ),
    },
    {
      header: 'Status',
      render: (row) => <LeaveStatusBadge status={row.status} />,
    },
    {
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          {onViewDetails && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onViewDetails(row)}
              className="px-2.5 py-1 text-xs"
              title="View Request Details"
            >
              <IconEye size={14} className="sm:mr-1" />
              <span className="hidden sm:inline">Details</span>
            </Button>
          )}
          {row.status === LEAVE_STATUS.PENDING && onApprove && (
            <Button
              variant="success"
              size="sm"
              onClick={() => onApprove(row)}
              className="px-2.5 py-1 text-xs font-medium"
              title="Approve Request"
            >
              <IconCheck size={14} className="sm:mr-1" />
              <span className="hidden sm:inline">Approve</span>
            </Button>
          )}
          {row.status === LEAVE_STATUS.PENDING && onReject && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => onReject(row)}
              className="px-2.5 py-1 text-xs font-medium"
              title="Reject Request"
            >
              <IconX size={14} className="sm:mr-1" />
              <span className="hidden sm:inline">Reject</span>
            </Button>
          )}
        </div>
      ),
    },
  ];

  return <Table columns={columns} data={requests} loading={loading} emptyMessage={emptyMessage} />;
}
