import React, { useState, useEffect, useMemo } from 'react';
import Button from '../common/Button';
import LeaveStatusBadge from './LeaveStatusBadge';
import { formatDate } from '../../utils/dateUtils';
import { LeaveRequest } from '../../types/leave';
import { PublicHoliday } from '../../types/admin';
import { adminService } from '../../services/adminService';
import { IconCalendar } from '../common/Icons';

export interface EmployeeCalendarProps {
  leaves?: LeaveRequest[];
  loading?: boolean;
  onViewDetails?: (leave: LeaveRequest) => void;
}

export default function EmployeeCalendar({
  leaves = [],
  loading = false,
  onViewDetails,
}: EmployeeCalendarProps): React.ReactElement {
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [holidays, setHolidays] = useState<PublicHoliday[]>([]);
  const [selectedDayEvents, setSelectedDayEvents] = useState<{
    dayStr: string;
    items: LeaveRequest[];
    holidays: PublicHoliday[];
  } | null>(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  useEffect(() => {
    async function fetchHolidays() {
      try {
        const res = await adminService.getHolidays();
        setHolidays(res.items || []);
      } catch {
        // Fallback silently if unauthenticated or endpoint failure
      }
    }
    fetchHolidays();
  }, []);

  const prevMonth = (): void => {
    setCurrentDate(new Date(year, month - 1, 1));
    setSelectedDayEvents(null);
  };

  const nextMonth = (): void => {
    setCurrentDate(new Date(year, month + 1, 1));
    setSelectedDayEvents(null);
  };

  const todayMonth = (): void => {
    setCurrentDate(new Date());
    setSelectedDayEvents(null);
  };

  const monthName = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });

  // Generate days in month for grid
  const calendarDays = useMemo(() => {
    const firstDayIndex = new Date(year, month, 1).getDay(); // 0 = Sunday
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();

    const days = [];

    // Previous month padding
    for (let i = firstDayIndex - 1; i >= 0; i--) {
      days.push({
        dateNumber: daysInPrevMonth - i,
        isCurrentMonth: false,
        dateObj: new Date(year, month - 1, daysInPrevMonth - i),
      });
    }

    // Current month
    for (let i = 1; i <= daysInMonth; i++) {
      days.push({
        dateNumber: i,
        isCurrentMonth: true,
        dateObj: new Date(year, month, i),
      });
    }

    // Next month padding
    const remaining = (7 - (days.length % 7)) % 7;
    for (let i = 1; i <= remaining; i++) {
      days.push({
        dateNumber: i,
        isCurrentMonth: false,
        dateObj: new Date(year, month + 1, i),
      });
    }

    return days;
  }, [year, month]);

  // Find applied leaves covering a date
  const getLeavesForDay = (dateObj: Date): LeaveRequest[] => {
    const target = new Date(dateObj);
    target.setHours(0, 0, 0, 0);

    return leaves.filter((e) => {
      if (e.status === 'CANCELLED') return false;
      const start = new Date(e.start_date);
      start.setHours(0, 0, 0, 0);
      const end = new Date(e.end_date);
      end.setHours(23, 59, 59, 999);
      return target >= start && target <= end;
    });
  };

  // Find public holidays for a date
  const getHolidaysForDay = (dateObj: Date): PublicHoliday[] => {
    const y = dateObj.getFullYear();
    const m = String(dateObj.getMonth() + 1).padStart(2, '0');
    const d = String(dateObj.getDate()).padStart(2, '0');
    const isoStr = `${y}-${m}-${d}`;
    return holidays.filter((h) => h.holiday_date === isoStr);
  };

  const todayStr = new Date().toISOString().split('T')[0];

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 h-80 animate-pulse">
        <div className="h-6 w-48 bg-slate-200 rounded mb-4" />
        <div className="h-64 bg-slate-100 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
      {/* Calendar Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <IconCalendar size={20} className="text-indigo-600" />
            <h3 className="text-lg font-bold text-slate-900">My Leave Calendar</h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">Applied leave dates and official company holidays for {monthName}</p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={todayMonth} className="text-xs">
            Today
          </Button>
          <Button variant="outline" size="sm" onClick={prevMonth} className="px-2 text-xs">
            &larr;
          </Button>
          <Button variant="outline" size="sm" onClick={nextMonth} className="px-2 text-xs">
            &rarr;
          </Button>
        </div>
      </div>

      {/* Days Header */}
      <div className="grid grid-cols-7 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider py-2 bg-slate-50 rounded-xl">
        <div>Sun</div>
        <div>Mon</div>
        <div>Tue</div>
        <div>Wed</div>
        <div>Thu</div>
        <div>Fri</div>
        <div>Sat</div>
      </div>

      {/* Calendar Days Grid */}
      <div className="grid grid-cols-7 gap-1 sm:gap-2">
        {calendarDays.map((cell, idx) => {
          const dayLeaves = getLeavesForDay(cell.dateObj);
          const dayHolidays = getHolidaysForDay(cell.dateObj);
          const y = cell.dateObj.getFullYear();
          const m = String(cell.dateObj.getMonth() + 1).padStart(2, '0');
          const d = String(cell.dateObj.getDate()).padStart(2, '0');
          const dateISO = `${y}-${m}-${d}`;
          const isToday = dateISO === todayStr;
          const hasEvents = dayLeaves.length > 0 || dayHolidays.length > 0;

          return (
            <div
              key={idx}
              onClick={() => {
                if (hasEvents) {
                  setSelectedDayEvents({
                    dayStr: formatDate(dateISO),
                    items: dayLeaves,
                    holidays: dayHolidays,
                  });
                }
              }}
              className={`min-h-[64px] sm:min-h-[78px] p-1.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                !cell.isCurrentMonth
                  ? 'bg-slate-50/40 text-slate-300 border-slate-100'
                  : dayHolidays.length > 0
                  ? 'bg-purple-50/50 border-purple-200/80'
                  : 'bg-white border-slate-200/80'
              } ${isToday ? 'ring-2 ring-indigo-500 border-indigo-500' : ''} ${
                hasEvents ? 'cursor-pointer hover:border-indigo-400 hover:shadow-xs' : ''
              }`}
            >
              <div className="flex items-center justify-between">
                <span
                  className={`text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center ${
                    isToday
                      ? 'bg-indigo-600 text-white'
                      : cell.isCurrentMonth
                      ? 'text-slate-800'
                      : 'text-slate-400'
                  }`}
                >
                  {cell.dateNumber}
                </span>
                <div className="flex items-center gap-1">
                  {dayHolidays.length > 0 && (
                    <span className="w-2 h-2 rounded-full bg-purple-500" title="Company Holiday" />
                  )}
                  {dayLeaves.length > 0 && (
                    <span
                      className={`w-2 h-2 rounded-full ${
                        dayLeaves.some((l) => l.status === 'APPROVED') ? 'bg-emerald-500' : 'bg-amber-500'
                      }`}
                    />
                  )}
                </div>
              </div>

              {/* Badges inside day cell */}
              <div className="space-y-1 mt-1 overflow-hidden">
                {/* Public Holiday Badge */}
                {dayHolidays.slice(0, 1).map((h) => (
                  <div
                    key={`h-${h.id}`}
                    className="text-[10px] leading-tight font-bold px-1.5 py-0.5 rounded truncate bg-purple-100 text-purple-950 border border-purple-200/80"
                    title={`Public Holiday: ${h.name}`}
                  >
                    🏖️ {h.name}
                  </div>
                ))}

                {/* Leave badges inside day cell */}
                {dayLeaves.slice(0, 1).map((ev) => {
                  const isApproved = ev.status === 'APPROVED';
                  return (
                    <div
                      key={ev.id}
                      className={`text-[10px] leading-tight font-medium px-1.5 py-0.5 rounded truncate border ${
                        isApproved
                          ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
                          : 'bg-amber-50 text-amber-900 border-amber-200'
                      }`}
                      title={`${ev.leave_type?.name || 'Leave'} (${ev.status})`}
                    >
                      {ev.leave_type?.name || 'Leave'}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Day Event Breakdown */}
      {selectedDayEvents && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-3">
          <div className="flex items-center justify-between font-bold text-slate-900">
            <span>Schedule for {selectedDayEvents.dayStr}</span>
            <button
              type="button"
              onClick={() => setSelectedDayEvents(null)}
              className="text-slate-500 hover:text-slate-800 text-xs"
            >
              Dismiss
            </button>
          </div>

          {/* Company Holidays */}
          {selectedDayEvents.holidays.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-purple-700 uppercase tracking-wider block">Official Holiday</span>
              {selectedDayEvents.holidays.map((h) => (
                <div key={h.id} className="bg-purple-50 p-3 rounded-lg border border-purple-200 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-purple-950 block text-xs">🏖️ {h.name}</span>
                    {h.description && <span className="text-purple-700 text-[11px] block mt-0.5">{h.description}</span>}
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-200 text-purple-900 border border-purple-300">
                    Company Holiday
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Applied Leaves */}
          {selectedDayEvents.items.length > 0 && (
            <div className="space-y-2">
              {selectedDayEvents.holidays.length > 0 && (
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block pt-1">My Applied Leaves</span>
              )}
              {selectedDayEvents.items.map((ev) => (
                <div key={ev.id} className="bg-white p-3 rounded-lg border border-slate-200 flex items-center justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <span className="font-semibold text-slate-900 block truncate">{ev.leave_type?.name || `Leave Type #${ev.leave_type_id}`}</span>
                    <span className="text-slate-500 text-[11px] block">
                      {formatDate(ev.start_date)} to {formatDate(ev.end_date)} ({ev.total_days} days)
                    </span>
                    {ev.reason && <span className="block text-[11px] text-slate-600 italic mt-0.5 truncate">"{ev.reason}"</span>}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <LeaveStatusBadge status={ev.status} />
                    {onViewDetails && (
                      <Button variant="outline" size="sm" onClick={() => onViewDetails(ev)}>
                        Details
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Status Legend */}
      <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-slate-100 text-xs text-slate-500">
        <span className="font-medium text-slate-600">Legend:</span>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block" />
          <span>Public Holiday</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
          <span>Approved Leave</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
          <span>Pending Approval</span>
        </div>
      </div>
    </div>
  );
}
