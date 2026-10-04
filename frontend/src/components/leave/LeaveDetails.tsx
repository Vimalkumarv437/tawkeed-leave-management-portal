import React from 'react';
import LeaveStatusBadge from './LeaveStatusBadge';
import { formatDate, formatDateTime } from '../../utils/dateUtils';
import { LeaveRequest } from '../../types/leave';
import { IconCalendar, IconClock, IconTags, IconUser, IconInfo } from '../common/Icons';

export interface LeaveDetailsProps {
  leave: LeaveRequest | null;
}

export default function LeaveDetails({ leave }: LeaveDetailsProps): React.ReactElement | null {
  if (!leave) return null;

  return (
    <div className="space-y-5 text-slate-800">
      {/* Header Banner inside Details */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-50 border border-slate-200">
        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">
            Request Reference
          </span>
          <h4 className="text-base font-bold text-slate-900">Request #{leave.id}</h4>
        </div>
        <LeaveStatusBadge status={leave.status} />
      </div>

      {/* Primary Details Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Leave Type */}
        <div className="p-3.5 rounded-xl border border-indigo-100 bg-indigo-50/30 flex items-start gap-3">
          <div className="p-2 rounded-lg bg-indigo-100 text-indigo-700 shrink-0">
            <IconTags size={20} />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium block">Leave Type Name</span>
            <span className="text-base font-bold text-slate-900 block mt-0.5">
              {leave.leave_type?.name || `Leave Type #${leave.leave_type_id}`}
            </span>
            {leave.leave_type?.code && (
              <span className="inline-block mt-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200/60">
                Code: {leave.leave_type.code}
              </span>
            )}
          </div>
        </div>

        {/* Total Working Days */}
        <div className="p-3.5 rounded-xl border border-slate-200/80 bg-white flex items-start gap-3">
          <div className="p-2 rounded-lg bg-amber-50 text-amber-600 border border-amber-100 shrink-0">
            <IconClock size={18} />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium block">Total Duration</span>
            <span className="text-sm font-bold text-slate-900 block mt-0.5">
              {leave.total_days} {Number(leave.total_days) === 1 ? 'working day' : 'working days'}
            </span>
            <span className="text-[11px] text-slate-400 font-medium">Inclusive of working schedule</span>
          </div>
        </div>

        {/* Start & End Dates */}
        <div className="p-3.5 rounded-xl border border-slate-200/80 bg-white flex items-start gap-3">
          <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100 shrink-0">
            <IconCalendar size={18} />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium block">Date Range</span>
            <span className="text-sm font-bold text-slate-900 block mt-0.5">
              {formatDate(leave.start_date)} – {formatDate(leave.end_date)}
            </span>
          </div>
        </div>

        {/* Submission Timestamp */}
        <div className="p-3.5 rounded-xl border border-slate-200/80 bg-white flex items-start gap-3">
          <div className="p-2 rounded-lg bg-slate-100 text-slate-600 border border-slate-200/80 shrink-0">
            <IconInfo size={18} />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium block">Submitted On</span>
            <span className="text-sm font-semibold text-slate-800 block mt-0.5">
              {formatDateTime(leave.created_at)}
            </span>
          </div>
        </div>
      </div>

      {/* Reason Block */}
      {leave.reason && (
        <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-1">
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider block">
            Reason for Request
          </span>
          <p className="text-xs leading-relaxed text-slate-700 italic bg-white p-3 rounded-lg border border-slate-200/60">
            "{leave.reason}"
          </p>
        </div>
      )}

      {/* Manager Decision Comment */}
      {leave.approval_comment && (
        <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200/80 space-y-1">
          <span className="text-xs font-semibold text-indigo-900 uppercase tracking-wider block">
            Manager Review Note
          </span>
          <p className="text-xs leading-relaxed text-indigo-950 bg-white p-3 rounded-lg border border-indigo-100">
            "{leave.approval_comment}"
          </p>
        </div>
      )}

      {/* Cancellation Reason */}
      {leave.cancellation_reason && (
        <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 space-y-1">
          <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider block">
            Cancellation Note
          </span>
          <p className="text-xs leading-relaxed text-slate-700 italic bg-white p-3 rounded-lg border border-slate-200/60">
            "{leave.cancellation_reason}"
          </p>
        </div>
      )}
    </div>
  );
}
