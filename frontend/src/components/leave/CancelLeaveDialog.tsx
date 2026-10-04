import React, { useState } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';
import { LeaveRequest, CancelLeavePayload } from '../../types/leave';

export interface CancelLeaveDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (leaveId: number, payload: CancelLeavePayload) => void;
  leave: LeaveRequest | null;
  loading?: boolean;
}

export default function CancelLeaveDialog({
  isOpen,
  onClose,
  onConfirm,
  leave,
  loading = false,
}: CancelLeaveDialogProps): React.ReactElement {
  const [reason, setReason] = useState<string>('');

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    if (leave) {
      onConfirm(leave.id, { reason: reason.trim() || undefined });
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Cancel Leave Request #${leave?.id}`}
      size="sm"
    >
      <form onSubmit={handleSubmit}>
        <p className="cancel-prompt">
          Are you sure you want to cancel this leave request?
        </p>
        <div className="form-group">
          <label htmlFor="cancel-reason" className="form-label">
            Reason for cancellation (optional):
          </label>
          <textarea
            id="cancel-reason"
            rows={3}
            value={reason}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setReason(e.target.value)}
            className="form-textarea"
            maxLength={1000}
          />
        </div>
        <div className="confirm-actions">
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Close
          </Button>
          <Button type="submit" variant="danger" loading={loading}>
            Confirm Cancellation
          </Button>
        </div>
      </form>
    </Modal>
  );
}
