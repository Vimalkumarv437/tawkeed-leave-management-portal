import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { ROLES } from '../../utils/constants';
import {
  IconLogo,
  IconDashboard,
  IconCalendar,
  IconCalendarPlus,
  IconWallet,
  IconInbox,
  IconUsers,
  IconTags,
  IconHoliday,
  IconHistory,
  IconX,
} from '../common/Icons';

export interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  end?: boolean;
}

export default function Sidebar({ isOpen = false, onClose }: SidebarProps): React.ReactElement {
  const { role } = useAuth();

  const getNavItems = (): NavItem[] => {
    switch (role) {
      case ROLES.ADMIN:
        return [
          { to: '/admin', label: 'Dashboard', icon: <IconDashboard size={18} />, end: true },
          { to: '/admin/users', label: 'Users', icon: <IconUsers size={18} /> },
          { to: '/admin/leave-types', label: 'Leave Types', icon: <IconTags size={18} /> },
          { to: '/admin/balances', label: 'Balances', icon: <IconWallet size={18} /> },
          { to: '/admin/holidays', label: 'Holidays', icon: <IconHoliday size={18} /> },
          { to: '/admin/audit-logs', label: 'Audit Logs', icon: <IconHistory size={18} /> },
        ];
      case ROLES.MANAGER:
        return [
          { to: '/manager', label: 'Dashboard', icon: <IconDashboard size={18} />, end: true },
          { to: '/manager/requests', label: 'Team Requests', icon: <IconInbox size={18} /> },
          { to: '/manager/calendar', label: 'Team Calendar', icon: <IconCalendar size={18} /> },
          { to: '/manager/leaves', label: 'My Leaves', icon: <IconCalendar size={18} /> },
          { to: '/manager/leaves/apply', label: 'Apply Leave', icon: <IconCalendarPlus size={18} /> },
          { to: '/manager/balance', label: 'My Balance', icon: <IconWallet size={18} /> },
        ];
      case ROLES.EMPLOYEE:
      default:
        return [
          { to: '/employee', label: 'Dashboard', icon: <IconDashboard size={18} />, end: true },
          { to: '/employee/leaves', label: 'My Leaves', icon: <IconCalendar size={18} /> },
          { to: '/employee/leaves/apply', label: 'Apply Leave', icon: <IconCalendarPlus size={18} /> },
          { to: '/employee/balance', label: 'My Balance', icon: <IconWallet size={18} /> },
        ];
    }
  };

  const navItems = getNavItems();

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-xs md:hidden transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:sticky top-0 left-0 z-40 h-screen w-64 bg-slate-900 text-slate-100 flex flex-col shrink-0 transition-transform duration-300 ease-in-out md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="sidebar-header flex items-center justify-between p-5 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="sidebar-logo-icon flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400">
              <IconLogo size={22} />
            </div>
            <div className="sidebar-brand-text flex flex-col">
              <span className="sidebar-brand-name font-bold text-sm tracking-tight text-white">
                Tawkeed Portal
              </span>
              <span className="sidebar-brand-sub text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
                Leave Management
              </span>
            </div>
          </div>
          {/* Close button on mobile */}
          <button
            type="button"
            className="md:hidden p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            <IconX size={18} />
          </button>
        </div>

        <nav className="sidebar-nav flex-1 overflow-y-auto px-3 py-4 space-y-1">
          <div className="sidebar-section-title text-[10px] uppercase font-bold tracking-wider text-slate-400 px-3 pb-2 pt-1">
            Navigation
          </div>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => onClose?.()}
              className={({ isActive }) =>
                `nav-link flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white font-semibold shadow-xs'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/70'
                }`
              }
            >
              <span className="nav-icon shrink-0">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer p-4 border-t border-slate-800 mt-auto">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Logged in as:</span>
            <div className="sidebar-badge-role px-2.5 py-1 rounded-md text-[11px] font-semibold tracking-wide bg-slate-800 text-indigo-300 border border-slate-700/60">
              {role || 'EMPLOYEE'}
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
