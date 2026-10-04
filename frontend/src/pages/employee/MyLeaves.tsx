import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/layout/PageHeader';
import LeaveTable from '../../components/leave/LeaveTable';
import Pagination from '../../components/common/Pagination';
import CancelLeaveDialog from '../../components/leave/CancelLeaveDialog';
import Modal from '../../components/common/Modal';
import LeaveDetails from '../../components/leave/LeaveDetails';
import Button from '../../components/common/Button';
import ErrorMessage from '../../components/common/ErrorMessage';
import { employeeService } from '../../services/employeeService';
import { leaveService } from '../../services/leaveService';
import { usePagination } from '../../hooks/usePagination';
import { useToast } from '../../context/ToastContext';
import { extractErrorMessage } from '../../utils/errorUtils';
import { LeaveRequest, CancelLeavePayload } from '../../types/leave';

export default function MyLeaves(): React.ReactElement {
  const navigate = useNavigate();
  const toast = useToast();
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [cancellingLeave, setCancellingLeave] = useState<LeaveRequest | null>(null);
  const [selectedDetailLeave, setSelectedDetailLeave] = useState<LeaveRequest | null>(null);
  const [cancelLoading, setCancelLoading] = useState<boolean>(false);
  const { page, limit, offset, total, totalPages, setTotal, goToPage } = usePagination(10);

  const fetchLeaves = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError('');
    try {
      const data = await employeeService.getMyLeaves(offset, limit);
      setLeaves(data.items || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [offset, limit, setTotal]);

  useEffect(() => {
    fetchLeaves();
  }, [fetchLeaves]);

  const handleCancelConfirm = async (requestId: number, data: CancelLeavePayload): Promise<void> => {
    setCancelLoading(true);
    try {
      await leaveService.cancelLeave(requestId, data);
      setCancellingLeave(null);
      toast.success('Leave request cancelled successfully.');
      fetchLeaves();
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setCancelLoading(false);
    }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="My Leave Requests"
        subtitle="Track status and history of your requested leaves"
        action={
          <Button variant="primary" onClick={() => navigate('/employee/leaves/apply')}>
            + Apply for Leave
          </Button>
        }
      />
      <ErrorMessage message={error} onDismiss={() => setError('')} />
      <LeaveTable
        leaves={leaves}
        loading={loading}
        onViewDetails={(row) => setSelectedDetailLeave(row)}
        onCancel={(row) => setCancellingLeave(row)}
      />
      <Pagination
        page={page}
        totalPages={totalPages}
        total={total}
        limit={limit}
        onPageChange={goToPage}
      />

      {/* Leave Details Modal */}
      {selectedDetailLeave && (
        <Modal
          isOpen={!!selectedDetailLeave}
          onClose={() => setSelectedDetailLeave(null)}
          title="Leave Request Details"
          subtitle={`Reference #${selectedDetailLeave.id}`}
          size="lg"
        >
          <LeaveDetails leave={selectedDetailLeave} />
          <div className="mt-6 flex justify-end pt-4 border-t border-slate-100">
            <Button variant="outline" onClick={() => setSelectedDetailLeave(null)}>
              Close
            </Button>
          </div>
        </Modal>
      )}

      {/* Cancel Leave Dialog */}
      {cancellingLeave && (
        <CancelLeaveDialog
          isOpen={!!cancellingLeave}
          onClose={() => setCancellingLeave(null)}
          onConfirm={handleCancelConfirm}
          leave={cancellingLeave}
          loading={cancelLoading}
        />
      )}
    </div>
  );
}
