import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PageHeader from '../../components/layout/PageHeader';
import LeaveDetails from '../../components/leave/LeaveDetails';
import Button from '../../components/common/Button';
import Loading from '../../components/common/Loading';
import ErrorMessage from '../../components/common/ErrorMessage';
import { leaveService } from '../../services/leaveService';
import { extractErrorMessage } from '../../utils/errorUtils';
import { LeaveRequest } from '../../types/leave';

export default function EmployeeLeaveDetailsPage(): React.ReactElement {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [leave, setLeave] = useState<LeaveRequest | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    async function fetchDetails(): Promise<void> {
      if (!id) return;
      try {
        const data = await leaveService.getLeaveById(parseInt(id, 10));
        setLeave(data);
      } catch (err: unknown) {
        setError(extractErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    fetchDetails();
  }, [id]);

  if (loading) return <Loading message="Loading leave details..." />;

  return (
    <div className="page-container">
      <PageHeader
        title={`Leave Request #${id}`}
        subtitle="Detailed view of your leave request"
        action={
          <Button variant="outline" onClick={() => navigate(-1)}>
            &larr; Back
          </Button>
        }
      />
      <ErrorMessage message={error} />
      {leave && <LeaveDetails leave={leave} />}
    </div>
  );
}
