import React from 'react';
import Table, { Column } from '../common/Table';
import Button from '../common/Button';
import { formatDate } from '../../utils/dateUtils';
import { PublicHoliday } from '../../types/admin';

export interface HolidayTableProps {
  holidays?: PublicHoliday[];
  loading?: boolean;
  onEdit?: (holiday: PublicHoliday) => void;
  onDelete?: (holiday: PublicHoliday) => void;
}

export default function HolidayTable({
  holidays = [],
  loading = false,
  onEdit,
  onDelete,
}: HolidayTableProps): React.ReactElement {
  const columns: Column<PublicHoliday>[] = [
    { header: 'ID', accessor: 'id' },
    { header: 'Date', render: (row) => formatDate(row.holiday_date) },
    { header: 'Holiday Name', accessor: 'name' },
    { header: 'Description', accessor: 'description' },
    {
      header: 'Actions',
      render: (row) => (
        <div className="table-actions">
          {onEdit && (
            <Button variant="outline" size="sm" onClick={() => onEdit(row)}>
              Edit
            </Button>
          )}
          {onDelete && (
            <Button variant="danger" size="sm" onClick={() => onDelete(row)}>
              Delete
            </Button>
          )}
        </div>
      ),
    },
  ];

  return <Table columns={columns} data={holidays} loading={loading} />;
}
