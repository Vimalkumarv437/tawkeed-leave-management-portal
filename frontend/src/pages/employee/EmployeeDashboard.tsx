import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../context/ToastContext';
import PageHeader from '../../components/layout/PageHeader';
import Button from '../../components/common/Button';
import BalanceCard from '../../components/balance/BalanceCard';
import LeaveTable from '../../components/leave/LeaveTable';
import UpcomingLeaveList from '../../components/leave/UpcomingLeaveList';
import EmployeeCalendar from '../../components/leave/EmployeeCalendar';
import QuickActions from '../../components/leave/QuickActions';
import Modal from '../../components/common/Modal';
import LeaveDetails from '../../components/leave/LeaveDetails';
import CancelLeaveDialog from '../../components/leave/CancelLeaveDialog';
import EmptyState from '../../components/common/EmptyState';
import {
  IconCalendar,
  IconBriefcase,
  IconClock,
  IconWallet,
  IconRefresh,
  IconPlus,
} from '../../components/common/Icons';
import { employeeService } from '../../services/employeeService';
import { leaveService } from '../../services/leaveService';
import { extractErrorMessage } from '../../utils/errorUtils';
import { LEAVE_STATUS } from '../../utils/constants';
import { LeaveBalance, LeaveRequest, CancelLeavePayload } from '../../types/leave';

export default function EmployeeDashboard(): React.ReactElement {
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();

  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [allLeaves, setAllLeaves] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Cancel dialog state
  const [cancellingLeave, setCancellingLeave] = useState<LeaveRequest | null>(null);
  const [selectedDetailLeave, setSelectedDetailLeave] = useState<LeaveRequest | null>(null);
  const [cancelLoading, setCancelLoading] = useState<boolean>(false);

  const currentYear = new Date().getFullYear();

  // Greeting helper based on local time
  const getGreeting = (): string => {
    const hour = new Date().getHours();
    let timeGreeting = 'Good morning';
    if (hour >= 12 && hour < 17) {
      timeGreeting = 'Good afternoon';
    } else if (hour >= 17) {
      timeGreeting = 'Good evening';
    }

    const name =
      user?.first_name ||
      (user?.email ? user.email.split('@')[0] : '') ||
      '';

    return name ? `${timeGreeting}, ${name}` : timeGreeting;
  };

  const loadDashboardData = useCallback(async (isRefresh: boolean = false): Promise<void> => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError('');

    try {
      const [balanceRes, leavesRes] = await Promise.all([
        employeeService.getMyBalances(currentYear, 0, 50),
        employeeService.getMyLeaves(0, 50),
      ]);

      const balanceItems = balanceRes.items || [];
      const leaveItems = leavesRes.items || [];

      setBalances(balanceItems);
      setAllLeaves(leaveItems);

      if (isRefresh) {
        toast.info('Leave information updated successfully.');
      }
    } catch (err: unknown) {
      const msg = extractErrorMessage(err, 'Unable to load your leave information.');
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [currentYear, toast]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Handle leave cancellation
  const handleCancelConfirm = async (
    requestId: number,
    data: CancelLeavePayload
  ): Promise<void> => {
    setCancelLoading(true);
    setError('');
    try {
      await leaveService.cancelLeave(requestId, data);
      setCancellingLeave(null);
      toast.success('Leave request cancelled successfully.');
      await loadDashboardData(true);
    } catch (err: unknown) {
      const msg = extractErrorMessage(err, 'Failed to cancel leave request.');
      setError(msg);
      toast.error(msg);
    } finally {
      setCancelLoading(false);
    }
  };

  // Aggregate summary stats safely from real balance data
  const totalAllocated = balances.reduce(
    (acc, b) => acc + Number(b.allocated_days || 0),
    0
  );
  const totalUsed = balances.reduce(
    (acc, b) => acc + Number(b.used_days || 0),
    0
  );
  const totalReserved = balances.reduce(
    (acc, b) => acc + Number(b.reserved_days || 0),
    0
  );
  const totalRemaining = balances.reduce((acc, b) => {
    const rem =
      b.remaining_days !== undefined
        ? Number(b.remaining_days)
        : Number(b.allocated_days || 0) -
          Number(b.used_days || 0) -
          Number(b.reserved_days || 0);
    return acc + rem;
  }, 0);

  const formatDays = (val: number): string => {
    return Number.isInteger(val) ? val.toString() : val.toFixed(1);
  };

  // Filtered requests for the recent table
  const filteredRecentLeaves = useMemo(() => {
    let list = allLeaves;
    if (statusFilter !== 'ALL') {
      list = list.filter((l) => l.status === statusFilter);
    }
    return list.slice(0, 5);
  }, [allLeaves, statusFilter]);

  // Status counts for filter tabs
  const statusCounts = useMemo(() => {
    return {
      ALL: allLeaves.length,
      [LEAVE_STATUS.PENDING]: allLeaves.filter((l) => l.status === LEAVE_STATUS.PENDING).length,
      [LEAVE_STATUS.APPROVED]: allLeaves.filter((l) => l.status === LEAVE_STATUS.APPROVED).length,
      [LEAVE_STATUS.CANCELLED]: allLeaves.filter((l) => l.status === LEAVE_STATUS.CANCELLED).length,
      [LEAVE_STATUS.REJECTED]: allLeaves.filter((l) => l.status === LEAVE_STATUS.REJECTED).length,
    };
  }, [allLeaves]);

  return (
    <div className="dashboard-container">
      {/* 1. Header Section */}
      <PageHeader
        title={getGreeting()}
        subtitle="Here's your live leave balance overview and scheduled time off."
        action={
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadDashboardData(true)}
              disabled={loading || refreshing}
              title="Refresh dashboard data"
              className="refresh-btn"
            >
              <IconRefresh
                size={16}
                className={refreshing ? 'animate-spin' : ''}
              />
              <span className="hidden-mobile">Refresh</span>
            </Button>
            <Button
              variant="primary"
              onClick={() => navigate('/employee/leaves/apply')}
            >
              <IconPlus size={16} className="mr-1" />
              <span>Apply for Leave</span>
            </Button>
          </div>
        }
      />

      {/* Error State with Retry Button */}
      {error && (
        <div className="alert-danger mb-6 flex items-center justify-between">
          <div>
            <strong>Error: </strong>
            <span>{error}</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadDashboardData(false)}
            disabled={loading}
          >
            Try Again
          </Button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading ? (
        <div className="dashboard-loading-skeleton">
          <div className="stats-summary-grid">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton-card skeleton-stat" />
            ))}
          </div>
          <div className="dashboard-main-split mt-6">
            <div className="skeleton-card skeleton-panel-large" />
            <div className="skeleton-card skeleton-panel-small" />
          </div>
        </div>
      ) : (
        <>
          {/* 2. Overall Leave Summary Stats */}
          <div className="stats-summary-grid">
            <div className="summary-stat-card stat-available">
              <div className="stat-header">
                <span className="stat-icon stat-icon-success">
                  <IconCalendar size={20} />
                </span>
                <span className="stat-label">Available Leave</span>
              </div>
              <div className="stat-value">
                <span className="stat-num">{formatDays(totalRemaining)}</span>
                <span className="stat-unit">days</span>
              </div>
              <p className="stat-hint">Ready to take in {currentYear}</p>
            </div>

            <div className="summary-stat-card stat-used">
              <div className="stat-header">
                <span className="stat-icon stat-icon-primary">
                  <IconBriefcase size={20} />
                </span>
                <span className="stat-label">Used Leave</span>
              </div>
              <div className="stat-value">
                <span className="stat-num">{formatDays(totalUsed)}</span>
                <span className="stat-unit">days</span>
              </div>
              <p className="stat-hint">Approved and taken</p>
            </div>

            <div className="summary-stat-card stat-pending">
              <div className="stat-header">
                <span className="stat-icon stat-icon-warning">
                  <IconClock size={20} />
                </span>
                <span className="stat-label">Pending Approval</span>
              </div>
              <div className="stat-value">
                <span className="stat-num">{formatDays(totalReserved)}</span>
                <span className="stat-unit">days</span>
              </div>
              <p className="stat-hint">Awaiting manager review</p>
            </div>

            <div className="summary-stat-card stat-allocated">
              <div className="stat-header">
                <span className="stat-icon stat-icon-secondary">
                  <IconWallet size={20} />
                </span>
                <span className="stat-label">Total Allocated</span>
              </div>
              <div className="stat-value">
                <span className="stat-num">{formatDays(totalAllocated)}</span>
                <span className="stat-unit">days</span>
              </div>
              <p className="stat-hint">Annual entitlement</p>
            </div>
          </div>

          {/* 3. Leave Balance Visualizations by Type */}
          <div className="dashboard-section mt-8">
            <div className="section-header flex justify-between items-center mb-4">
              <div>
                <h3 className="section-title">Leave Balances</h3>
                <p className="section-subtitle">
                  Allocation breakdown and usage quotas for {currentYear}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/employee/balance')}
              >
                View Full Balance
              </Button>
            </div>

            {balances.length === 0 ? (
              <EmptyState
                title="No leave balance available"
                message="No leave allowances have been assigned for this year yet."
                icon={<IconWallet size={36} className="text-slate-400" />}
              />
            ) : (
              <div className="balance-cards-grid">
                {balances.map((b) => (
                  <BalanceCard
                    key={b.id}
                    title={b.leave_type?.name || `Leave Type #${b.leave_type_id}`}
                    code={b.leave_type?.code}
                    allocated={b.allocated_days}
                    used={b.used_days}
                    reserved={b.reserved_days}
                    remaining={b.remaining_days}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Interactive Employee Personal Leave Calendar Card */}
          <div className="dashboard-section mt-8">
            <EmployeeCalendar
              leaves={allLeaves}
              loading={loading}
              onViewDetails={(leave) => setSelectedDetailLeave(leave)}
            />
          </div>

          {/* 4 & 6. Two-Column Layout: Upcoming Leave & Quick Actions */}
          <div className="dashboard-two-column-grid mt-8">
            {/* Upcoming Leave */}
            <div className="dashboard-card panel-upcoming">
              <div className="panel-header">
                <div>
                  <h3 className="panel-title">Upcoming Leave</h3>
                  <p className="panel-subtitle">Your approved upcoming scheduled time off</p>
                </div>
              </div>
              <div className="panel-body">
                <UpcomingLeaveList
                  leaves={allLeaves}
                  onViewDetails={(leave) =>
                    setSelectedDetailLeave(leave)
                  }
                  onApplyLeave={() => navigate('/employee/leaves/apply')}
                />
              </div>
            </div>

            {/* Quick Actions */}
            <div className="dashboard-card panel-actions">
              <div className="panel-header">
                <div>
                  <h3 className="panel-title">Quick Actions</h3>
                  <p className="panel-subtitle">Frequently used employee services</p>
                </div>
              </div>
              <div className="panel-body">
                <QuickActions />
              </div>
            </div>
          </div>

          {/* 5. Recent Leave Requests with Filter Tabs */}
          <div className="dashboard-section mt-8">
            <div className="section-header flex flex-col md:flex-row justify-between items-start md:items-center gap-3 mb-4">
              <div>
                <h3 className="section-title">Recent Leave Requests</h3>
                <p className="section-subtitle">
                  Your most recent leave submissions and live manager approval status
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/employee/leaves')}
              >
                View All Requests ({allLeaves.length})
              </Button>
            </div>

            {/* Filter Tabs */}
            <div className="status-filter-tabs mb-4">
              <button
                type="button"
                className={`filter-tab ${statusFilter === 'ALL' ? 'active' : ''}`}
                onClick={() => setStatusFilter('ALL')}
              >
                All <span className="tab-badge">{statusCounts.ALL}</span>
              </button>
              <button
                type="button"
                className={`filter-tab ${statusFilter === LEAVE_STATUS.PENDING ? 'active' : ''}`}
                onClick={() => setStatusFilter(LEAVE_STATUS.PENDING)}
              >
                Pending <span className="tab-badge">{statusCounts[LEAVE_STATUS.PENDING]}</span>
              </button>
              <button
                type="button"
                className={`filter-tab ${statusFilter === LEAVE_STATUS.APPROVED ? 'active' : ''}`}
                onClick={() => setStatusFilter(LEAVE_STATUS.APPROVED)}
              >
                Approved <span className="tab-badge">{statusCounts[LEAVE_STATUS.APPROVED]}</span>
              </button>
              <button
                type="button"
                className={`filter-tab ${statusFilter === LEAVE_STATUS.CANCELLED ? 'active' : ''}`}
                onClick={() => setStatusFilter(LEAVE_STATUS.CANCELLED)}
              >
                Cancelled <span className="tab-badge">{statusCounts[LEAVE_STATUS.CANCELLED]}</span>
              </button>
              <button
                type="button"
                className={`filter-tab ${statusFilter === LEAVE_STATUS.REJECTED ? 'active' : ''}`}
                onClick={() => setStatusFilter(LEAVE_STATUS.REJECTED)}
              >
                Rejected <span className="tab-badge">{statusCounts[LEAVE_STATUS.REJECTED]}</span>
              </button>
            </div>

            <div className="dashboard-card">
              <LeaveTable
                leaves={filteredRecentLeaves}
                emptyMessage={
                  statusFilter === 'ALL'
                    ? 'When you apply for leave, your requests will appear here.'
                    : `No ${statusFilter.toLowerCase()} leave requests found.`
                }
                onViewDetails={(row) =>
                  setSelectedDetailLeave(row)
                }
                onCancel={(row) => setCancellingLeave(row)}
              />
            </div>
          </div>
        </>
      )}

      {/* Details Modal */}
      {selectedDetailLeave && (
        <Modal
          isOpen={!!selectedDetailLeave}
          onClose={() => setSelectedDetailLeave(null)}
          title="Leave Request Details"
          subtitle={`Reference #${selectedDetailLeave.id}`}
          size="lg"
        >
          <LeaveDetails leave={selectedDetailLeave} />
          <div className="mt-6 flex justify-end pt-4 border-t border-slate-100">
            <Button variant="outline" onClick={() => setSelectedDetailLeave(null)}>
              Close
            </Button>
          </div>
        </Modal>
      )}

      {/* Cancel Confirmation Dialog */}
      {cancellingLeave && (
        <CancelLeaveDialog
          isOpen={!!cancellingLeave}
          onClose={() => setCancellingLeave(null)}
          onConfirm={handleCancelConfirm}
          leave={cancellingLeave}
          loading={cancelLoading}
        />
      )}
    </div>
  );
}
