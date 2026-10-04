import React, { useState, useEffect } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import TeamCalendar from '../../components/manager/TeamCalendar';
import Loading from '../../components/common/Loading';
import ErrorMessage from '../../components/common/ErrorMessage';
import { managerService } from '../../services/managerService';
import { extractErrorMessage } from '../../utils/errorUtils';
import { LeaveRequest } from '../../types/leave';

export default function TeamCalendarPage(): React.ReactElement {
  const [events, setEvents] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    async function fetchCalendar(): Promise<void> {
      try {
        const data = await managerService.getTeamCalendar({ offset: 0, limit: 100 });
        setEvents(data.items || []);
      } catch (err: unknown) {
        setError(extractErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    fetchCalendar();
  }, []);

  if (loading) return <Loading message="Loading team calendar..." />;

  return (
    <div className="page-container">
      <PageHeader
        title="Team Calendar"
        subtitle="Overview of approved leaves across your team"
      />
      <ErrorMessage message={error} />
      <TeamCalendar events={events} />
    </div>
  );
}
