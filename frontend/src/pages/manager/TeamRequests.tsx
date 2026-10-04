import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/layout/PageHeader';
import ApprovalTable from '../../components/manager/ApprovalTable';
import ApprovalDialog from '../../components/manager/ApprovalDialog';
import Pagination from '../../components/common/Pagination';
import Select from '../../components/common/Select';
import ErrorMessage from '../../components/common/ErrorMessage';
import { managerService } from '../../services/managerService';
import { usePagination } from '../../hooks/usePagination';
import { LEAVE_STATUS } from '../../utils/constants';
import { extractErrorMessage } from '../../utils/errorUtils';
import { LeaveRequest, LeaveDecisionPayload, LeaveStatus } from '../../types/leave';

export default function TeamRequests(): React.ReactElement {
  const navigate = useNavigate();
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [dialogState, setDialogState] = useState<{
    isOpen: boolean;
    request: LeaveRequest | null;
    type: 'approve' | 'reject';
  }>({
    isOpen: false,
    request: null,
    type: 'approve',
  });
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const { page, limit, offset, total, totalPages, setTotal, goToPage } = usePagination(10);

  const fetchTeamRequests = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError('');
    try {
      const params = {
        offset,
        limit,
        status: (statusFilter || undefined) as LeaveStatus | undefined,
      };
      const data = await managerService.getTeamRequests(params);
      setRequests(data.items || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [offset, limit, statusFilter, setTotal]);

  useEffect(() => {
    fetchTeamRequests();
  }, [fetchTeamRequests]);

  const handleDecisionConfirm = async (requestId: number, data: LeaveDecisionPayload): Promise<void> => {
    setActionLoading(true);
    try {
      if (dialogState.type === 'approve') {
        await managerService.approveRequest(requestId, data);
      } else {
        await managerService.rejectRequest(requestId, data);
      }
      setDialogState({ isOpen: false, request: null, type: 'approve' });
      fetchTeamRequests();
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Team Leave Requests"
        subtitle="Review, approve, or reject leave requests from your direct team"
        action={
          <div className="status-filter-wrapper w-48">
            <Select
              value={statusFilter}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setStatusFilter(e.target.value)}
              placeholder="All Statuses"
              options={[
                { value: LEAVE_STATUS.PENDING, label: 'Pending Only' },
                { value: LEAVE_STATUS.APPROVED, label: 'Approved Only' },
                { value: LEAVE_STATUS.REJECTED, label: 'Rejected Only' },
                { value: LEAVE_STATUS.CANCELLED, label: 'Cancelled Only' },
              ]}
            />
          </div>
        }
      />
      <ErrorMessage message={error} onDismiss={() => setError('')} />
      <ApprovalTable
        requests={requests}
        loading={loading}
        onApprove={(req) => setDialogState({ isOpen: true, request: req, type: 'approve' })}
        onReject={(req) => setDialogState({ isOpen: true, request: req, type: 'reject' })}
        onViewDetails={(req) => navigate(`/manager/requests/${req.id}`)}
      />
      <Pagination
        page={page}
        totalPages={totalPages}
        total={total}
        limit={limit}
        onPageChange={goToPage}
      />
      {dialogState.isOpen && (
        <ApprovalDialog
          isOpen={dialogState.isOpen}
          onClose={() => setDialogState({ isOpen: false, request: null, type: 'approve' })}
          onConfirm={handleDecisionConfirm}
          request={dialogState.request}
          type={dialogState.type}
          loading={actionLoading}
        />
      )}
    </div>
  );
}
