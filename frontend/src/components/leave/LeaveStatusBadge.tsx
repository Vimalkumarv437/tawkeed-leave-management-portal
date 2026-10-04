import React from 'react';
import { LeaveStatus } from '../../types/leave';
import { LEAVE_STATUS } from '../../utils/constants';

export interface LeaveStatusBadgeProps {
  status: LeaveStatus | string;
}

export default function LeaveStatusBadge({ status }: LeaveStatusBadgeProps): React.ReactElement {
  const getBadgeClass = (): string => {
    switch (status) {
      case LEAVE_STATUS.APPROVED:
        return 'badge-success';
      case LEAVE_STATUS.PENDING:
        return 'badge-warning';
      case LEAVE_STATUS.REJECTED:
        return 'badge-danger';
      case LEAVE_STATUS.CANCELLED:
        return 'badge-muted';
      default:
        return 'badge-secondary';
    }
  };

  return (
    <span className={`status-badge ${getBadgeClass()}`}>
      {status || 'UNKNOWN'}
    </span>
  );
}
