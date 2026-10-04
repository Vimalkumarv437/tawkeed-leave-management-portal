import React from 'react';
import Table, { Column } from '../common/Table';
import { LeaveBalance } from '../../types/leave';

export interface BalanceTableProps {
  balances?: LeaveBalance[];
  loading?: boolean;
}

export default function BalanceTable({
  balances = [],
  loading = false,
}: BalanceTableProps): React.ReactElement {
  const columns: Column<LeaveBalance>[] = [
    {
      header: 'Leave Type',
      render: (row) => row.leave_type?.name || `Type #${row.leave_type_id}`,
    },
    { header: 'Year', accessor: 'year' },
    { header: 'Allocated Days', accessor: 'allocated_days' },
    { header: 'Used Days', accessor: 'used_days' },
    { header: 'Reserved Days', accessor: 'reserved_days' },
    {
      header: 'Remaining Days',
      render: (row) => {
        const remaining =
          Number(row.allocated_days) -
          Number(row.used_days) -
          Number(row.reserved_days);
        return <strong className="text-success">{remaining.toFixed(2)}</strong>;
      },
    },
  ];

  return <Table columns={columns} data={balances} loading={loading} />;
}
