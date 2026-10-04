import React from 'react';
import Table, { Column } from '../common/Table';
import { formatDateTime } from '../../utils/dateUtils';
import { AuditLog } from '../../types/admin';

export interface AuditLogTableProps {
  logs?: AuditLog[];
  loading?: boolean;
}

export default function AuditLogTable({
  logs = [],
  loading = false,
}: AuditLogTableProps): React.ReactElement {
  const getActionBadgeClass = (action: string): string => {
    const act = action.toUpperCase();
    if (act.includes('CREATE') || act.includes('APPROVE') || act.includes('REACTIVATE')) {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
    if (act.includes('DELETE') || act.includes('REJECT') || act.includes('DEACTIVATE')) {
      return 'bg-rose-50 text-rose-700 border-rose-200';
    }
    if (act.includes('UPDATE') || act.includes('CANCEL')) {
      return 'bg-amber-50 text-amber-700 border-amber-200';
    }
    return 'bg-indigo-50 text-indigo-700 border-indigo-200';
  };

  const renderDetails = (details: Record<string, unknown> | null | undefined): React.ReactNode => {
    if (!details || Object.keys(details).length === 0) {
      return <span className="text-slate-400 italic text-xs">None</span>;
    }

    return (
      <div className="flex flex-wrap gap-1.5 max-w-lg py-0.5">
        {Object.entries(details).map(([key, val]) => {
          let displayVal = val;
          if (typeof val === 'object' && val !== null) {
            const objVal = val as Record<string, unknown>;
            if (objVal.from !== undefined && objVal.to !== undefined) {
              displayVal = `${String(objVal.from)} → ${String(objVal.to)}`;
            } else {
              displayVal = JSON.stringify(val);
            }
          }
          return (
            <span
              key={key}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-xs border border-slate-200/80 shadow-2xs"
            >
              <span className="text-slate-500 font-semibold capitalize">
                {key.replace(/_/g, ' ')}:
              </span>
              <span className="text-slate-900 font-medium">{String(displayVal)}</span>
            </span>
          );
        })}
      </div>
    );
  };

  const columns: Column<AuditLog>[] = [
    { header: 'ID', accessor: 'id' },
    {
      header: 'Timestamp',
      render: (row) => (
        <span className="text-xs text-slate-600 font-medium whitespace-nowrap">
          {formatDateTime(row.created_at)}
        </span>
      ),
    },
    {
      header: 'User',
      render: (row) => {
        const name = row.user
          ? `${row.user.first_name} ${row.user.last_name}`
          : 'System Actor';

        const initials = row.user
          ? `${row.user.first_name[0] || ''}${row.user.last_name[0] || ''}`.toUpperCase()
          : 'SYS';

        return (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-slate-100 border border-slate-200 text-slate-700 font-semibold text-xs flex items-center justify-center shrink-0">
              {initials}
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-slate-800">{name}</span>
              {row.user?.email && (
                <span className="text-[11px] text-slate-500">{row.user.email}</span>
              )}
            </div>
          </div>
        );
      },
    },
    {
      header: 'Action',
      render: (row) => (
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getActionBadgeClass(
            row.action
          )}`}
        >
          {row.action.replace(/_/g, ' ')}
        </span>
      ),
    },
    {
      header: 'Entity Type',
      render: (row) => (
        <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 capitalize">
          {row.entity_type.replace(/_/g, ' ')}
        </span>
      ),
    },
    {
      header: 'Details',
      render: (row) => renderDetails(row.details),
    },
  ];

  return <Table columns={columns} data={logs} loading={loading} />;
}
