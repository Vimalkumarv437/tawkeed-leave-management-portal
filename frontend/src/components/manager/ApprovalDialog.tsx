import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import { LeaveRequest, LeaveDecisionPayload } from '../../types/leave';
import { formatDate } from '../../utils/dateUtils';
import { IconCheckCircle, IconXCircle, IconCalendar, IconUser, IconTags, IconClock } from '../common/Icons';

export interface ApprovalDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (requestId: number, payload: LeaveDecisionPayload) => Promise<void> | void;
  request: LeaveRequest | null;
  type?: 'approve' | 'reject';
  loading?: boolean;
}

export default function ApprovalDialog({
  isOpen,
  onClose,
  onConfirm,
  request,
  type = 'approve',
  loading = false,
}: ApprovalDialogProps): React.ReactElement {
  const [comment, setComment] = useState<string>('');
  const isApprove = type === 'approve';

  useEffect(() => {
    if (isOpen) {
      setComment('');
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    if (request) {
      onConfirm(request.id, { comment: comment.trim() || undefined });
    }
  };

  const employeeName = request?.user
    ? `${request.user.first_name} ${request.user.last_name}`
    : `Employee #${request?.user_id || ''}`;

  const leaveTypeName = request?.leave_type?.name || `Leave Type #${request?.leave_type_id || ''}`;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`${isApprove ? 'Approve' : 'Reject'} Leave Request`}
      subtitle={`Request #${request?.id || ''}`}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Request Overview Card */}
        {request && (
          <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="flex items-center gap-2">
                <IconUser size={16} className="text-slate-400 shrink-0" />
                <div>
                  <span className="text-slate-500 block">Employee</span>
                  <span className="font-semibold text-slate-800">{employeeName}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <IconTags size={16} className="text-slate-400 shrink-0" />
                <div>
                  <span className="text-slate-500 block">Leave Type</span>
                  <span className="font-semibold text-slate-800">{leaveTypeName}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <IconCalendar size={16} className="text-slate-400 shrink-0" />
                <div>
                  <span className="text-slate-500 block">Dates</span>
                  <span className="font-semibold text-slate-800">
                    {formatDate(request.start_date)} – {formatDate(request.end_date)}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <IconClock size={16} className="text-slate-400 shrink-0" />
                <div>
                  <span className="text-slate-500 block">Duration</span>
                  <span className="font-semibold text-slate-800">{request.total_days} working days</span>
                </div>
              </div>
            </div>

            {request.reason && (
              <div className="pt-2 border-t border-slate-200/80 text-xs">
                <span className="text-slate-500 block mb-0.5">Employee Reason:</span>
                <p className="text-slate-700 italic bg-white p-2.5 rounded-lg border border-slate-200/60">
                  "{request.reason}"
                </p>
              </div>
            )}
          </div>
        )}

        <div className="flex items-start gap-3 p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/80 text-amber-900 text-xs">
          {isApprove ? (
            <IconCheckCircle size={18} className="text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <IconXCircle size={18} className="text-rose-600 shrink-0 mt-0.5" />
          )}
          <p>
            Are you sure you want to <strong className="font-semibold">{isApprove ? 'approve' : 'reject'}</strong> this leave request? This action will update the employee's leave status and balance allocation.
          </p>
        </div>

        <div className="form-group">
          <label htmlFor="decision-comment" className="form-label text-xs font-semibold text-slate-700 mb-1.5 block">
            {isApprove ? 'Manager Comment (Optional)' : 'Rejection Reason (Optional)'}
          </label>
          <textarea
            id="decision-comment"
            rows={3}
            value={comment}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setComment(e.target.value)}
            className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-colors"
            placeholder={
              isApprove
                ? 'Add an optional note or confirmation details for the employee...'
                : 'Provide feedback or a reason for rejecting this request...'
            }
            maxLength={1000}
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200">
          <Button type="button" variant="outline" onClick={onClose} disabled={loading} className="px-4">
            Cancel
          </Button>
          <Button
            type="submit"
            variant={isApprove ? 'success' : 'danger'}
            loading={loading}
            className="px-5 font-medium"
          >
            {isApprove ? 'Confirm Approval' : 'Confirm Rejection'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
