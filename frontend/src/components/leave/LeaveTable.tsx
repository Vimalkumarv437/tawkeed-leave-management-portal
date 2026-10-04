import React from 'react';
import Table, { Column } from '../common/Table';
import LeaveStatusBadge from './LeaveStatusBadge';
import Button from '../common/Button';
import { formatDate } from '../../utils/dateUtils';
import { LEAVE_STATUS, HALF_DAY_TYPE } from '../../utils/constants';
import { LeaveRequest } from '../../types/leave';

export interface LeaveTableProps {
  leaves?: LeaveRequest[];
  loading?: boolean;
  emptyMessage?: string;
  onViewDetails?: (leave: LeaveRequest) => void;
  onCancel?: (leave: LeaveRequest) => void;
}

export default function LeaveTable({
  leaves = [],
  loading = false,
  emptyMessage = 'No leave requests found.',
  onViewDetails,
  onCancel,
}: LeaveTableProps): React.ReactElement {
  const renderDateRange = (row: LeaveRequest): React.ReactNode => {
    const isSingleDay = row.start_date === row.end_date;
    const dateText = isSingleDay
      ? formatDate(row.start_date)
      : `${formatDate(row.start_date)} – ${formatDate(row.end_date)}`;

    let halfDayLabel = '';
    if (row.start_half_day && row.start_half_day !== HALF_DAY_TYPE.NONE) {
      halfDayLabel = row.start_half_day === HALF_DAY_TYPE.FIRST_HALF ? 'First Half' : 'Second Half';
    } else if (row.end_half_day && row.end_half_day !== HALF_DAY_TYPE.NONE) {
      halfDayLabel = row.end_half_day === HALF_DAY_TYPE.FIRST_HALF ? 'First Half' : 'Second Half';
    }

    return (
      <div className="leave-date-cell">
        <span className="font-medium text-slate-800">{dateText}</span>
        {halfDayLabel && <span className="half-day-tag">{halfDayLabel}</span>}
      </div>
    );
  };

  const columns: Column<LeaveRequest>[] = [
    {
      header: 'Leave Type',
      render: (row) => {
        const name = row.leave_type?.name || `Leave Type #${row.leave_type_id}`;
        const code = row.leave_type?.code;
        return (
          <div className="flex flex-col text-left">
            <span className="font-semibold text-slate-900 text-sm">{name}</span>
            {code && (
              <span className="text-[11px] text-slate-400 font-medium tracking-wide">
                {code}
              </span>
            )}
          </div>
        );
      },
    },
    {
      header: 'Dates',
      render: renderDateRange,
    },
    {
      header: 'Days',
      render: (row) => {
        const days = Number(row.total_days);
        return (
          <span className="font-semibold text-slate-700">
            {Number.isInteger(days) ? days : days.toFixed(1)} {days === 1 ? 'day' : 'days'}
          </span>
        );
      },
    },
    {
      header: 'Status',
      render: (row) => <LeaveStatusBadge status={row.status} />,
    },
    {
      header: 'Requested On',
      render: (row) => (
        <span className="text-muted text-sm">{formatDate(row.created_at)}</span>
      ),
    },
    {
      header: 'Actions',
      render: (row) => (
        <div className="table-actions">
          {onViewDetails && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onViewDetails(row)}
            >
              Details
            </Button>
          )}
          {onCancel && row.status === LEAVE_STATUS.PENDING && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => onCancel(row)}
            >
              Cancel
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      data={leaves}
      loading={loading}
      emptyMessage={emptyMessage}
    />
  );
}

