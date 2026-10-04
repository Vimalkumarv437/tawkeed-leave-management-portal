import React, { useState, useEffect } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import AuditLogTable from '../../components/admin/AuditLogTable';
import Pagination from '../../components/common/Pagination';
import Select from '../../components/common/Select';
import ErrorMessage from '../../components/common/ErrorMessage';
import { adminService } from '../../services/adminService';
import { usePagination } from '../../hooks/usePagination';
import { AUDIT_ACTIONS } from '../../utils/constants';
import { extractErrorMessage } from '../../utils/errorUtils';
import { AuditLog, AuditAction } from '../../types/admin';

export default function AuditLogs(): React.ReactElement {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [actionFilter, setActionFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const { page, limit, offset, total, totalPages, setTotal, goToPage } = usePagination(20);

  const fetchAuditLogs = async (): Promise<void> => {
    setLoading(true);
    setError('');
    try {
      const params = {
        offset,
        limit,
        action: (actionFilter || undefined) as AuditAction | undefined,
      };
      const data = await adminService.getAuditLogs(params);
      setLogs(data.items || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [offset, limit, actionFilter]);

  return (
    <div className="page-container">
      <PageHeader
        title="Audit Logs"
        subtitle="Immutable audit trail of all leave management and administrative actions"
        action={
          <div className="action-filter-wrapper w-56">
            <Select
              value={actionFilter}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setActionFilter(e.target.value)}
              placeholder="All Actions"
              options={Object.values(AUDIT_ACTIONS).map((action) => ({
                value: action,
                label: action,
              }))}
            />
          </div>
        }
      />
      <ErrorMessage message={error} onDismiss={() => setError('')} />
      <AuditLogTable logs={logs} loading={loading} />
      <Pagination
        page={page}
        totalPages={totalPages}
        total={total}
        limit={limit}
        onPageChange={goToPage}
      />
    </div>
  );
}
