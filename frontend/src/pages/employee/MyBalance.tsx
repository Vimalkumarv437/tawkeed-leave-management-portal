import React, { useState, useEffect, useMemo } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import BalanceTable from '../../components/balance/BalanceTable';
import Select from '../../components/common/Select';
import ErrorMessage from '../../components/common/ErrorMessage';
import EmptyState from '../../components/common/EmptyState';
import { employeeService } from '../../services/employeeService';
import { extractErrorMessage } from '../../utils/errorUtils';
import { LeaveBalance } from '../../types/leave';
import { IconWallet, IconCheckCircle, IconClock, IconCalendar } from '../../components/common/Icons';

export default function MyBalance(): React.ReactElement {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState<number>(currentYear);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    async function fetchBalances(): Promise<void> {
      setLoading(true);
      setError('');
      try {
        const data = await employeeService.getMyBalances(year);
        setBalances(data.items || []);
      } catch (err: unknown) {
        setError(extractErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    fetchBalances();
  }, [year]);

  // Summary Totals
  const summary = useMemo(() => {
    return balances.reduce(
      (acc, b) => {
        const allocated = Number(b.allocated_days) || 0;
        const used = Number(b.used_days) || 0;
        const reserved = Number(b.reserved_days) || 0;
        const remaining = allocated - used - reserved;

        return {
          totalAllocated: acc.totalAllocated + allocated,
          totalUsed: acc.totalUsed + used,
          totalReserved: acc.totalReserved + reserved,
          totalRemaining: acc.totalRemaining + remaining,
        };
      },
      { totalAllocated: 0, totalUsed: 0, totalReserved: 0, totalRemaining: 0 }
    );
  }, [balances]);

  return (
    <div className="space-y-6 text-slate-800">
      <PageHeader
        title="My Leave Balances"
        subtitle={`Annual allowance and leave summary for ${year}`}
        action={
          <div className="year-selector w-36">
            <Select
              value={year}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setYear(parseInt(e.target.value, 10))}
              options={[
                { value: currentYear - 1, label: String(currentYear - 1) },
                { value: currentYear, label: String(currentYear) },
                { value: currentYear + 1, label: String(currentYear + 1) },
              ]}
            />
          </div>
        }
      />

      <ErrorMessage message={error} onDismiss={() => setError('')} />

      {/* Summary Cards Header */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Remaining */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Remaining</span>
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200/60">
              <IconWallet size={20} />
            </div>
          </div>
          <div>
            <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
              {summary.totalRemaining.toFixed(1)}
            </span>
            <span className="text-xs font-medium text-slate-500 ml-1">days</span>
          </div>
        </div>

        {/* Total Allocated */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Annual Allowance</span>
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-200/60">
              <IconCalendar size={20} />
            </div>
          </div>
          <div>
            <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
              {summary.totalAllocated.toFixed(1)}
            </span>
            <span className="text-xs font-medium text-slate-500 ml-1">days</span>
          </div>
        </div>

        {/* Total Used */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Used Leave</span>
            <div className="p-2 rounded-xl bg-purple-50 text-purple-600 border border-purple-200/60">
              <IconCheckCircle size={20} />
            </div>
          </div>
          <div>
            <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
              {summary.totalUsed.toFixed(1)}
            </span>
            <span className="text-xs font-medium text-slate-500 ml-1">days</span>
          </div>
        </div>

        {/* Total Reserved / Pending */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending / Reserved</span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600 border border-amber-200/60">
              <IconClock size={20} />
            </div>
          </div>
          <div>
            <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
              {summary.totalReserved.toFixed(1)}
            </span>
            <span className="text-xs font-medium text-slate-500 ml-1">days</span>
          </div>
        </div>
      </div>

      {/* Leave Type Cards Grid */}
      {!loading && balances.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {balances.map((b) => {
            const allocated = Number(b.allocated_days) || 0;
            const used = Number(b.used_days) || 0;
            const reserved = Number(b.reserved_days) || 0;
            const remaining = allocated - used - reserved;

            return (
              <div key={b.id} className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-slate-900 text-base">{b.leave_type?.name || `Leave Type #${b.leave_type_id}`}</h4>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
                    {year}
                  </span>
                </div>

                <div>
                  <div className="flex items-baseline justify-between mb-1.5">
                    <span className="text-2xl font-extrabold text-emerald-600">{remaining.toFixed(1)}</span>
                    <span className="text-xs text-slate-500">of {allocated.toFixed(1)} days available</span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden flex">
                    <div
                      className="bg-purple-500 h-full transition-all duration-300"
                      style={{ width: `${allocated > 0 ? (used / allocated) * 100 : 0}%` }}
                      title={`Used: ${used} days`}
                    />
                    <div
                      className="bg-amber-400 h-full transition-all duration-300"
                      style={{ width: `${allocated > 0 ? (reserved / allocated) * 100 : 0}%` }}
                      title={`Reserved: ${reserved} days`}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Allocated</span>
                    <span className="font-semibold text-slate-700">{allocated.toFixed(1)} d</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Used</span>
                    <span className="font-semibold text-slate-700">{used.toFixed(1)} d</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Reserved</span>
                    <span className="font-semibold text-slate-700">{reserved.toFixed(1)} d</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Detailed Balance Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
        <h3 className="text-base font-bold text-slate-900 mb-4">Detailed Balance Breakdown</h3>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-12 rounded-xl bg-slate-100 animate-pulse" />
            ))}
          </div>
        ) : balances.length === 0 ? (
          <EmptyState title="No balances found" message={`No leave balances configured for ${year}.`} />
        ) : (
          <BalanceTable balances={balances} loading={false} />
        )}
      </div>
    </div>
  );
}
