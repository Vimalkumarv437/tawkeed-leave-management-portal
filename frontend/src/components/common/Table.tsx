import React, { ReactNode } from 'react';
import Loading from './Loading';
import EmptyState from './EmptyState';

export interface Column<T> {
  header: string;
  accessor?: keyof T | string;
  key?: string;
  render?: (row: T) => ReactNode;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export default function Table<T extends Record<string, any>>({
  columns = [],
  data = [],
  loading = false,
  emptyMessage = 'No records found.',
  className = '',
}: TableProps<T>) {
  if (loading) {
    return <Loading message="Loading data..." />;
  }

  if (!data || data.length === 0) {
    return <EmptyState message={emptyMessage} />;
  }

  return (
    <div className={`table-responsive ${className}`}>
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col, idx) => (
              <th key={col.key || String(col.accessor) || idx}>{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIdx) => (
            <tr key={row.id || rowIdx}>
              {columns.map((col, colIdx) => (
                <td key={col.key || String(col.accessor) || colIdx}>
                  {col.render
                    ? col.render(row)
                    : col.accessor
                    ? row[col.accessor as string]
                    : null}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
