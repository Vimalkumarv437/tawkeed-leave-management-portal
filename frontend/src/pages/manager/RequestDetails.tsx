import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PageHeader from '../../components/layout/PageHeader';
import LeaveDetails from '../../components/leave/LeaveDetails';
import ApprovalDialog from '../../components/manager/ApprovalDialog';
import Button from '../../components/common/Button';
import Loading from '../../components/common/Loading';
import ErrorMessage from '../../components/common/ErrorMessage';
import { managerService } from '../../services/managerService';
import { LEAVE_STATUS } from '../../utils/constants';
import { extractErrorMessage } from '../../utils/errorUtils';
import { LeaveRequest, LeaveDecisionPayload } from '../../types/leave';

export default function RequestDetails(): React.ReactElement {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [request, setRequest] = useState<LeaveRequest | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [dialogState, setDialogState] = useState<{
    isOpen: boolean;
    type: 'approve' | 'reject';
  }>({
    isOpen: false,
    type: 'approve',
  });
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  const fetchRequestDetails = useCallback(async (): Promise<void> => {
    if (!id) return;
    try {
      // Find request from team requests
      const data = await managerService.getTeamRequests({ limit: 100 });
      const found = (data.items || []).find((r: LeaveRequest) => r.id === parseInt(id, 10));
      if (!found) {
        setError('Leave request not found in your team records.');
      } else {
        setRequest(found);
      }
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchRequestDetails();
  }, [fetchRequestDetails]);

  const handleDecision = async (requestId: number, payload: LeaveDecisionPayload): Promise<void> => {
    setActionLoading(true);
    try {
      if (dialogState.type === 'approve') {
        await managerService.approveRequest(requestId, payload);
      } else {
        await managerService.rejectRequest(requestId, payload);
      }
      setDialogState({ isOpen: false, type: 'approve' });
      fetchRequestDetails();
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <Loading message="Loading request details..." />;

  return (
    <div className="page-container">
      <PageHeader
        title={`Team Request #${id}`}
        subtitle="Review employee leave request details"
        action={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate(-1)}>
              &larr; Back
            </Button>
            {request?.status === LEAVE_STATUS.PENDING && (
              <>
                <Button
                  variant="success"
                  onClick={() => setDialogState({ isOpen: true, type: 'approve' })}
                >
                  Approve
                </Button>
                <Button
                  variant="danger"
                  onClick={() => setDialogState({ isOpen: true, type: 'reject' })}
                >
                  Reject
                </Button>
              </>
            )}
          </div>
        }
      />
      <ErrorMessage message={error} />
      {request && <LeaveDetails leave={request} />}
      {dialogState.isOpen && request && (
        <ApprovalDialog
          isOpen={dialogState.isOpen}
          onClose={() => setDialogState({ isOpen: false, type: 'approve' })}
          onConfirm={handleDecision}
          request={request}
          type={dialogState.type}
          loading={actionLoading}
        />
      )}
    </div>
  );
}
