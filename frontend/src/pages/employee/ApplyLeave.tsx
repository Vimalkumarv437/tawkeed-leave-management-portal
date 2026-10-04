import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/layout/PageHeader';
import LeaveForm from '../../components/leave/LeaveForm';
import Loading from '../../components/common/Loading';
import { adminService } from '../../services/adminService';
import { leaveService } from '../../services/leaveService';
import { useToast } from '../../context/ToastContext';
import { useAuth } from '../../hooks/useAuth';
import { ROLES } from '../../utils/constants';
import { extractErrorMessage } from '../../utils/errorUtils';
import { LeaveType, CreateLeavePayload } from '../../types/leave';

export default function ApplyLeave(): React.ReactElement {
  const navigate = useNavigate();
  const toast = useToast();
  const { role } = useAuth();
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    async function loadLeaveTypes(): Promise<void> {
      try {
        const data = await adminService.getLeaveTypes({ is_active: true });
        const items = (data as { items?: LeaveType[] }).items || (Array.isArray(data) ? data : []);
        setLeaveTypes(items);
      } catch (err: unknown) {
        setError(extractErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    loadLeaveTypes();
  }, []);

  const handleApply = async (formData: CreateLeavePayload): Promise<void> => {
    setSubmitting(true);
    setError('');
    try {
      await leaveService.createLeave(formData);
      toast.success('Leave request submitted successfully!');
      if (role === ROLES.MANAGER) {
        navigate('/manager/leaves');
      } else {
        navigate('/employee/leaves');
      }
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Loading message="Loading leave application..." />;

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <PageHeader
        title="Apply for Leave"
        subtitle="Submit a new leave request for processing"
      />
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 sm:p-8">
        <LeaveForm
          leaveTypes={leaveTypes}
          onSubmit={handleApply}
          loading={submitting}
          error={error}
        />
      </div>
    </div>
  );
}
