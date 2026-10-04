import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/common/Button';
import ApprovalTable from '../../components/manager/ApprovalTable';
import ApprovalDialog from '../../components/manager/ApprovalDialog';
import Modal from '../../components/common/Modal';
import LeaveDetails from '../../components/leave/LeaveDetails';
import ErrorMessage from '../../components/common/ErrorMessage';
import EmptyState from '../../components/common/EmptyState';
import LeaveStatusBadge from '../../components/leave/LeaveStatusBadge';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../context/ToastContext';
import { managerService } from '../../services/managerService';
import { LEAVE_STATUS } from '../../utils/constants';
import { extractErrorMessage } from '../../utils/errorUtils';
import { formatDate } from '../../utils/dateUtils';
import { LeaveRequest, LeaveDecisionPayload } from '../../types/leave';
import {
  IconCalendar,
  IconClock,
  IconCheckCircle,
  IconUsers,
  IconInbox,
  IconChevronRight,
} from '../../components/common/Icons';

export default function ManagerDashboard(): React.ReactElement {
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();

  const [pendingRequests, setPendingRequests] = useState<LeaveRequest[]>([]);
  const [allTeamRequests, setAllTeamRequests] = useState<LeaveRequest[]>([]);
  const [calendarEvents, setCalendarEvents] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  // Dialog & Details Modal State
  const [dialogState, setDialogState] = useState<{
    isOpen: boolean;
    request: LeaveRequest | null;
    type: 'approve' | 'reject';
  }>({
    isOpen: false,
    request: null,
    type: 'approve',
  });
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  const [selectedDetailRequest, setSelectedDetailRequest] = useState<LeaveRequest | null>(null);

  // Time-of-day greeting
  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  }, []);

  const managerFirstName = user?.first_name ? user.first_name : 'Manager';

  // Fetch real data from backend
  const fetchDashboardData = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError('');
    try {
      const [pendingRes, allRequestsRes, calendarRes] = await Promise.all([
        managerService.getTeamRequests({ status: LEAVE_STATUS.PENDING, offset: 0, limit: 20 }),
        managerService.getTeamRequests({ offset: 0, limit: 100 }),
        managerService.getTeamCalendar({ offset: 0, limit: 100 }),
      ]);

      setPendingRequests(pendingRes.items || []);
      setAllTeamRequests(allRequestsRes.items || []);
      setCalendarEvents(calendarRes.items || []);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Derived real backend metrics
  const metrics = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth();

    const in30Days = new Date(today);
    in30Days.setDate(today.getDate() + 30);

    // 1. Pending count
    const pendingCount = pendingRequests.length;

    // 2. Approved this month
    const approvedThisMonthCount = allTeamRequests.filter((r) => {
      if (r.status !== LEAVE_STATUS.APPROVED) return false;
      const d = new Date(r.start_date);
      return d.getFullYear() === currentYear && d.getMonth() === currentMonth;
    }).length;

    // 3. On leave today (from calendar events)
    const onLeaveTodayList = calendarEvents.filter((r) => {
      if (r.status !== LEAVE_STATUS.APPROVED) return false;
      const start = new Date(r.start_date);
      start.setHours(0, 0, 0, 0);
      const end = new Date(r.end_date);
      end.setHours(23, 59, 59, 999);
      return today >= start && today <= end;
    });

    // 4. Upcoming leave (approved, starts in the future within 30 days)
    const upcomingLeaveList = calendarEvents.filter((r) => {
      if (r.status !== LEAVE_STATUS.APPROVED) return false;
      const start = new Date(r.start_date);
      start.setHours(0, 0, 0, 0);
      return start > today && start <= in30Days;
    }).sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime());

    return {
      pendingCount,
      approvedThisMonthCount,
      onLeaveTodayCount: onLeaveTodayList.length,
      onLeaveTodayList,
      upcomingLeaveCount: upcomingLeaveList.length,
      upcomingLeaveList,
    };
  }, [pendingRequests, allTeamRequests, calendarEvents]);

  // Approval / Rejection Handler
  const handleDecisionConfirm = async (requestId: number, data: LeaveDecisionPayload): Promise<void> => {
    setActionLoading(true);
    try {
      if (dialogState.type === 'approve') {
        await managerService.approveRequest(requestId, data);
        toast.success(`Leave request #${requestId} has been approved.`);
      } else {
        await managerService.rejectRequest(requestId, data);
        toast.success(`Leave request #${requestId} has been rejected.`);
      }

      setDialogState({ isOpen: false, request: null, type: 'approve' });
      setSelectedDetailRequest(null);
      await fetchDashboardData();
    } catch (err: unknown) {
      toast.error(extractErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6 text-slate-800">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <span className="text-xs font-semibold text-indigo-600 tracking-wider uppercase mb-1 block">
            {greeting}, {managerFirstName}
          </span>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Team Leave Overview</h1>
          <p className="text-sm text-slate-500 mt-1">
            Review leave requests and monitor your team's availability.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Button variant="outline" onClick={() => navigate('/manager/calendar')}>
            <IconCalendar size={16} className="mr-2 text-slate-500" />
            <span>View Team Calendar</span>
          </Button>
          <Button variant="primary" onClick={() => navigate('/manager/requests')}>
            <IconInbox size={16} className="mr-2" />
            <span>Review Requests</span>
          </Button>
        </div>
      </div>

      <ErrorMessage message={error} onDismiss={() => setError('')} />

      {/* Summary Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-slate-100 animate-pulse border border-slate-200/60" />
          ))
        ) : (
          <>
            {/* Card 1: Pending */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between hover:border-amber-300 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Requests</span>
                <div className="p-2 rounded-xl bg-amber-50 text-amber-600 border border-amber-200/60">
                  <IconClock size={20} />
                </div>
              </div>
              <div>
                <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
                  {metrics.pendingCount}
                </span>
                <p className="text-xs font-medium text-amber-600 mt-1 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block" />
                  Needs attention
                </p>
              </div>
            </div>

            {/* Card 2: Approved This Month */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between hover:border-emerald-300 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Approved</span>
                <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200/60">
                  <IconCheckCircle size={20} />
                </div>
              </div>
              <div>
                <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
                  {metrics.approvedThisMonthCount}
                </span>
                <p className="text-xs font-medium text-slate-500 mt-1">This month</p>
              </div>
            </div>

            {/* Card 3: On Leave Today */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between hover:border-indigo-300 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">On Leave Today</span>
                <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600 border border-indigo-200/60">
                  <IconUsers size={20} />
                </div>
              </div>
              <div>
                <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
                  {metrics.onLeaveTodayCount}
                </span>
                <p className="text-xs font-medium text-slate-500 mt-1">Team members</p>
              </div>
            </div>

            {/* Card 4: Upcoming Leave */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col justify-between hover:border-purple-300 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Upcoming Leave</span>
                <div className="p-2 rounded-xl bg-purple-50 text-purple-600 border border-purple-200/60">
                  <IconCalendar size={20} />
                </div>
              </div>
              <div>
                <span className="text-3xl font-extrabold text-slate-900 tracking-tight">
                  {metrics.upcomingLeaveCount}
                </span>
                <p className="text-xs font-medium text-slate-500 mt-1">Next 30 days</p>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Primary Section: Pending Leave Requests */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/50">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Pending Leave Requests</h2>
            <p className="text-xs text-slate-500 mt-0.5">Requests waiting for your review</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/manager/requests')}
            className="self-start sm:self-auto text-xs"
          >
            <span>View all team requests</span>
            <IconChevronRight size={14} className="ml-1" />
          </Button>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-12 rounded-xl bg-slate-100 animate-pulse" />
              ))}
            </div>
          ) : pendingRequests.length === 0 ? (
            <EmptyState
              title="No pending requests"
              message="You're all caught up. There are no leave requests waiting for your review."
              icon={<IconCheckCircle size={40} className="text-emerald-500" />}
              action={
                <Button variant="outline" size="sm" onClick={() => navigate('/manager/calendar')}>
                  View Team Calendar
                </Button>
              }
            />
          ) : (
            <ApprovalTable
              requests={pendingRequests}
              loading={false}
              onApprove={(req) => setDialogState({ isOpen: true, request: req, type: 'approve' })}
              onReject={(req) => setDialogState({ isOpen: true, request: req, type: 'reject' })}
              onViewDetails={(req) => setSelectedDetailRequest(req)}
            />
          )}
        </div>
      </div>

      {/* Grid Section: Team Availability & Upcoming Team Leave */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Team Availability (On Leave Today) */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Team Availability</h3>
              <p className="text-xs text-slate-500 mt-0.5">Team members currently away today</p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60">
              {metrics.onLeaveTodayCount} Away
            </span>
          </div>

          <div className="flex-1">
            {loading ? (
              <div className="space-y-3">
                <div className="h-14 rounded-xl bg-slate-100 animate-pulse" />
              </div>
            ) : metrics.onLeaveTodayList.length === 0 ? (
              <div className="py-8 text-center bg-slate-50/60 rounded-xl border border-dashed border-slate-200">
                <p className="text-xs font-semibold text-slate-600">No team members are currently on leave today.</p>
                <p className="text-[11px] text-slate-400 mt-1">Everyone is available.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {metrics.onLeaveTodayList.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs shrink-0 border border-indigo-200">
                        {item.user ? `${item.user.first_name[0]}${item.user.last_name[0]}` : 'U'}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-slate-900 truncate">
                          {item.user ? `${item.user.first_name} ${item.user.last_name}` : `User #${item.user_id}`}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          {item.leave_type?.name || 'Leave'} &bull; {item.total_days} {Number(item.total_days) === 1 ? 'day' : 'days'}
                        </p>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-xs font-medium text-slate-700 block">
                        {formatDate(item.start_date)} – {formatDate(item.end_date)}
                      </span>
                      <LeaveStatusBadge status={item.status} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Upcoming Team Leave */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Upcoming Team Leave</h3>
              <p className="text-xs text-slate-500 mt-0.5">Approved leave starting in the next 30 days</p>
            </div>
            <Button variant="outline" size="sm" onClick={() => navigate('/manager/calendar')} className="text-xs">
              Calendar
            </Button>
          </div>

          <div className="flex-1">
            {loading ? (
              <div className="space-y-3">
                <div className="h-14 rounded-xl bg-slate-100 animate-pulse" />
              </div>
            ) : metrics.upcomingLeaveList.length === 0 ? (
              <div className="py-8 text-center bg-slate-50/60 rounded-xl border border-dashed border-slate-200">
                <p className="text-xs font-semibold text-slate-600">No upcoming team leave scheduled.</p>
                <p className="text-[11px] text-slate-400 mt-1">There are no upcoming leave dates in the next 30 days.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {metrics.upcomingLeaveList.slice(0, 4).map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-xs shrink-0 border border-purple-200">
                        {item.user ? `${item.user.first_name[0]}${item.user.last_name[0]}` : 'U'}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-slate-900 truncate">
                          {item.user ? `${item.user.first_name} ${item.user.last_name}` : `User #${item.user_id}`}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          {item.leave_type?.name || 'Leave'} &bull; {item.total_days} {Number(item.total_days) === 1 ? 'day' : 'days'}
                        </p>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-xs font-semibold text-slate-800 block">
                        {formatDate(item.start_date)}
                      </span>
                      <span className="text-[11px] text-slate-500 block">to {formatDate(item.end_date)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Approval / Rejection Confirmation Dialog */}
      {dialogState.isOpen && (
        <ApprovalDialog
          isOpen={dialogState.isOpen}
          onClose={() => setDialogState({ isOpen: false, request: null, type: 'approve' })}
          onConfirm={handleDecisionConfirm}
          request={dialogState.request}
          type={dialogState.type}
          loading={actionLoading}
        />
      )}

      {/* Quick Request Details Modal */}
      {selectedDetailRequest && (
        <Modal
          isOpen={!!selectedDetailRequest}
          onClose={() => setSelectedDetailRequest(null)}
          title={`Leave Request #${selectedDetailRequest.id}`}
          size="lg"
        >
          <div className="space-y-6">
            <LeaveDetails leave={selectedDetailRequest} />

            {selectedDetailRequest.status === LEAVE_STATUS.PENDING && (
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
                <Button
                  variant="danger"
                  onClick={() => {
                    const req = selectedDetailRequest;
                    setSelectedDetailRequest(null);
                    setDialogState({ isOpen: true, request: req, type: 'reject' });
                  }}
                >
                  Reject Request
                </Button>
                <Button
                  variant="success"
                  onClick={() => {
                    const req = selectedDetailRequest;
                    setSelectedDetailRequest(null);
                    setDialogState({ isOpen: true, request: req, type: 'approve' });
                  }}
                >
                  Approve Request
                </Button>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
