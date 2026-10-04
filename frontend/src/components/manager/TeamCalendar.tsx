import React, { useState, useEffect, useMemo } from 'react';
import Table, { Column } from '../common/Table';
import Button from '../common/Button';
import LeaveStatusBadge from '../leave/LeaveStatusBadge';
import { formatDate } from '../../utils/dateUtils';
import { LeaveRequest } from '../../types/leave';
import { PublicHoliday } from '../../types/admin';
import { adminService } from '../../services/adminService';
import { IconCalendar, IconChevronRight } from '../common/Icons';

export interface TeamCalendarProps {
  events?: LeaveRequest[];
  loading?: boolean;
}

export default function TeamCalendar({
  events = [],
  loading = false,
}: TeamCalendarProps): React.ReactElement {
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
      } catch (err) {
        // Fallback silently
      }
    }
    fetchHolidays();
  }, []);

  // Month navigation
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

    // Previous month padding days
    for (let i = firstDayIndex - 1; i >= 0; i--) {
      days.push({
        dateNumber: daysInPrevMonth - i,
        isCurrentMonth: false,
        dateObj: new Date(year, month - 1, daysInPrevMonth - i),
      });
    }

    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      days.push({
        dateNumber: i,
        isCurrentMonth: true,
        dateObj: new Date(year, month, i),
      });
    }

    // Next month padding days to fill grid cells
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

  // Map events to calendar days
  const getEventsForDay = (dateObj: Date): LeaveRequest[] => {
    const target = new Date(dateObj);
    target.setHours(0, 0, 0, 0);

    return events.filter((e) => {
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

  const columns: Column<LeaveRequest>[] = [
    {
      header: 'Team Member',
      render: (row) => {
        const name = row.user ? `${row.user.first_name} ${row.user.last_name}` : `User #${row.user_id}`;
        return (
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs shrink-0">
              {row.user ? `${row.user.first_name[0]}${row.user.last_name[0]}` : 'U'}
            </div>
            <span className="font-semibold text-slate-900 text-xs sm:text-sm">{name}</span>
          </div>
        );
      },
    },
    {
      header: 'Leave Type',
      render: (row) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
          {row.leave_type?.name || `Type #${row.leave_type_id}`}
        </span>
      ),
    },
    { header: 'Start Date', render: (row) => formatDate(row.start_date) },
    { header: 'End Date', render: (row) => formatDate(row.end_date) },
    { header: 'Total Days', render: (row) => `${row.total_days} days` },
    { header: 'Status', render: (row) => <LeaveStatusBadge status={row.status} /> },
  ];

  return (
    <div className="space-y-6 text-slate-800">
      {/* Monthly Interactive Calendar Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        {/* Calendar Header Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <IconCalendar size={22} className="text-indigo-600" />
            <h3 className="text-lg font-bold text-slate-900">{monthName}</h3>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={todayMonth} className="text-xs">
              Today
            </Button>
            <Button variant="outline" size="sm" onClick={prevMonth} className="px-2 text-xs">
              &larr; Prev
            </Button>
            <Button variant="outline" size="sm" onClick={nextMonth} className="px-2 text-xs">
              Next &rarr;
            </Button>
          </div>
        </div>

        {/* Day of Week Header */}
        <div className="grid grid-cols-7 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider py-2 bg-slate-50 rounded-xl">
          <div>Sun</div>
          <div>Mon</div>
          <div>Tue</div>
          <div>Wed</div>
          <div>Thu</div>
          <div>Fri</div>
          <div>Sat</div>
        </div>

        {/* Calendar Day Cells */}
        <div className="grid grid-cols-7 gap-1 sm:gap-2">
          {calendarDays.map((cell, idx) => {
            const dayEvents = getEventsForDay(cell.dateObj);
            const dayHolidays = getHolidaysForDay(cell.dateObj);
            const y = cell.dateObj.getFullYear();
            const m = String(cell.dateObj.getMonth() + 1).padStart(2, '0');
            const d = String(cell.dateObj.getDate()).padStart(2, '0');
            const dateISO = `${y}-${m}-${d}`;
            const isToday = dateISO === todayStr;
            const hasActivity = dayEvents.length > 0 || dayHolidays.length > 0;

            return (
              <div
                key={idx}
                onClick={() => {
                  if (hasActivity) {
                    setSelectedDayEvents({
                      dayStr: formatDate(dateISO),
                      items: dayEvents,
                      holidays: dayHolidays,
                    });
                  }
                }}
                className={`min-h-[72px] sm:min-h-[88px] p-1.5 sm:p-2 rounded-xl border text-left transition-all flex flex-col justify-between ${
                  !cell.isCurrentMonth
                    ? 'bg-slate-50/40 text-slate-300 border-slate-100'
                    : dayHolidays.length > 0
                    ? 'bg-purple-50/50 border-purple-200/80'
                    : 'bg-white border-slate-200/80'
                } ${isToday ? 'ring-2 ring-indigo-500 border-indigo-500' : ''} ${
                  hasActivity ? 'cursor-pointer hover:border-indigo-400 hover:shadow-xs' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center ${
                      isToday ? 'bg-indigo-600 text-white' : cell.isCurrentMonth ? 'text-slate-800' : 'text-slate-400'
                    }`}
                  >
                    {cell.dateNumber}
                  </span>
                  <div className="flex items-center gap-1">
                    {dayHolidays.length > 0 && (
                      <span className="w-2 h-2 rounded-full bg-purple-500" title="Public Holiday" />
                    )}
                    {dayEvents.length > 0 && (
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
                        {dayEvents.length}
                      </span>
                    )}
                  </div>
                </div>

                {/* Event Pills & Holiday Badges */}
                <div className="space-y-1 mt-1 overflow-hidden">
                  {dayHolidays.slice(0, 1).map((h) => (
                    <div
                      key={`h-${h.id}`}
                      className="text-[10px] leading-tight font-bold px-1.5 py-0.5 rounded bg-purple-100 text-purple-950 border border-purple-200/80 truncate"
                      title={`Company Holiday: ${h.name}`}
                    >
                      🏖️ {h.name}
                    </div>
                  ))}
                  {dayEvents.slice(0, 2).map((ev) => (
                    <div
                      key={ev.id}
                      className="text-[10px] leading-tight font-medium px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-900 border border-indigo-200/60 truncate"
                      title={`${ev.user?.first_name || 'User'} - ${ev.leave_type?.name || 'Leave'}`}
                    >
                      {ev.user ? `${ev.user.first_name}` : 'Leave'} ({ev.leave_type?.code || 'LV'})
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Highlight details box if a day is clicked */}
        {selectedDayEvents && (
          <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-200 text-xs space-y-3">
            <div className="flex items-center justify-between font-bold text-indigo-900">
              <span>Team & Holiday Schedule for {selectedDayEvents.dayStr}</span>
              <button
                type="button"
                onClick={() => setSelectedDayEvents(null)}
                className="text-indigo-600 hover:text-indigo-800 text-xs"
              >
                Dismiss
              </button>
            </div>

            {/* Official Company Holidays */}
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

            {/* Team Members On Leave */}
            {selectedDayEvents.items.length > 0 && (
              <div className="space-y-1.5">
                {selectedDayEvents.holidays.length > 0 && (
                  <span className="text-[11px] font-semibold text-indigo-700 uppercase tracking-wider block pt-1">Team Members Away</span>
                )}
                {selectedDayEvents.items.map((ev) => (
                  <div key={ev.id} className="bg-white p-2.5 rounded-lg border border-indigo-100 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-slate-900 block">
                        {ev.user ? `${ev.user.first_name} ${ev.user.last_name}` : `User #${ev.user_id}`}
                      </span>
                      <span className="text-slate-500 text-[11px]">
                        {ev.leave_type?.name} ({formatDate(ev.start_date)} - {formatDate(ev.end_date)})
                      </span>
                    </div>
                    <LeaveStatusBadge status={ev.status} />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Scheduled Team Leaves List / Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
        <h3 className="text-base font-bold text-slate-900 mb-4">All Approved Team Leaves</h3>
        <Table
          columns={columns}
          data={events}
          loading={loading}
          emptyMessage="No team leaves scheduled."
        />
      </div>
    </div>
  );
}
