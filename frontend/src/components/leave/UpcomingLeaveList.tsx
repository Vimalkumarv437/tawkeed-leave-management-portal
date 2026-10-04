import React from 'react';
import Button from '../common/Button';
import LeaveStatusBadge from './LeaveStatusBadge';
import EmptyState from '../common/EmptyState';
import { IconCalendar } from '../common/Icons';
import { formatDate } from '../../utils/dateUtils';
import { LEAVE_STATUS, HALF_DAY_TYPE } from '../../utils/constants';
import { LeaveRequest } from '../../types/leave';

export interface UpcomingLeaveListProps {
  leaves?: LeaveRequest[];
  onViewDetails?: (leave: LeaveRequest) => void;
  onApplyLeave?: () => void;
}

export default function UpcomingLeaveList({
  leaves = [],
  onViewDetails,
  onApplyLeave,
}: UpcomingLeaveListProps): React.ReactElement {
  // Filter for approved upcoming leaves
  const todayStr = new Date().toISOString().split('T')[0];

  const upcomingApprovedLeaves = leaves
    .filter((l) => l.status === LEAVE_STATUS.APPROVED && l.end_date >= todayStr)
    .sort((a, b) => a.start_date.localeCompare(b.start_date));

  if (upcomingApprovedLeaves.length === 0) {
    return (
      <EmptyState
        title="No upcoming leave"
        message="Plan some time off when you need it."
        icon={<IconCalendar size={36} className="text-slate-400" />}
        action={
          onApplyLeave ? (
            <Button variant="primary" size="sm" onClick={onApplyLeave}>
              + Apply for Leave
            </Button>
          ) : null
        }
      />
    );
  }

  return (
    <div className="upcoming-leaves-list">
      {upcomingApprovedLeaves.map((leave) => {
        const isSingleDay = leave.start_date === leave.end_date;
        const dateRangeStr = isSingleDay
          ? formatDate(leave.start_date)
          : `${formatDate(leave.start_date)} – ${formatDate(leave.end_date)}`;

        const totalDays = Number(leave.total_days);
        const daysLabel = `${Number.isInteger(totalDays) ? totalDays : totalDays.toFixed(1)} ${
          totalDays === 1 ? 'day' : 'days'
        }`;

        let halfDayText = '';
        if (leave.start_half_day && leave.start_half_day !== HALF_DAY_TYPE.NONE) {
          halfDayText =
            leave.start_half_day === HALF_DAY_TYPE.FIRST_HALF ? 'First Half' : 'Second Half';
        } else if (leave.end_half_day && leave.end_half_day !== HALF_DAY_TYPE.NONE) {
          halfDayText =
            leave.end_half_day === HALF_DAY_TYPE.FIRST_HALF ? 'First Half' : 'Second Half';
        }

        return (
          <div key={leave.id} className="upcoming-leave-card">
            <div className="upcoming-leave-left">
              <div className="upcoming-leave-icon">
                <IconCalendar size={18} className="text-blue-600" />
              </div>
              <div className="upcoming-leave-info">
                <div className="flex items-center gap-2">
                  <h5 className="upcoming-leave-type">
                    {leave.leave_type?.name || `Leave Type #${leave.leave_type_id}`}
                  </h5>
                  <LeaveStatusBadge status={leave.status} />
                </div>
                <div className="upcoming-leave-dates">
                  <span>{dateRangeStr}</span>
                  <span className="upcoming-leave-separator">•</span>
                  <span className="upcoming-leave-duration">{daysLabel}</span>
                  {halfDayText && (
                    <>
                      <span className="upcoming-leave-separator">•</span>
                      <span className="half-day-tag">{halfDayText}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            {onViewDetails && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onViewDetails(leave)}
                className="upcoming-leave-btn"
              >
                View
              </Button>
            )}
          </div>
        );
      })}
    </div>
  );
}
