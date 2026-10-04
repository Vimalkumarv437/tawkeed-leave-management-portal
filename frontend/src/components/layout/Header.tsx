import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import Button from '../common/Button';
import { IconLogout, IconMenu } from '../common/Icons';

export interface HeaderProps {
  onToggleSidebar?: () => void;
}

export default function Header({ onToggleSidebar }: HeaderProps): React.ReactElement {
  const { user, role, logout } = useAuth();

  const getInitials = (): string => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    if (user?.first_name) {
      return user.first_name.slice(0, 2).toUpperCase();
    }
    if (user?.email) {
      return user.email.slice(0, 2).toUpperCase();
    }
    return 'EP';
  };

  const displayName =
    user?.first_name && user?.last_name
      ? `${user.first_name} ${user.last_name}`
      : user?.email
      ? user.email.split('@')[0]
      : 'Employee';

  return (
    <header className="header-container bg-white border-b border-slate-200 px-4 md:px-8 flex items-center justify-between h-16 shrink-0 z-30">
      <div className="header-left flex items-center gap-3">
        {onToggleSidebar && (
          <button
            type="button"
            className="md:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors focus:outline-hidden"
            onClick={onToggleSidebar}
            aria-label="Toggle navigation menu"
          >
            <IconMenu size={20} />
          </button>
        )}
        <div className="portal-breadcrumb flex items-center gap-2 text-xs md:text-sm font-medium">
          <span className="breadcrumb-brand text-slate-400">Portal</span>
          <span className="breadcrumb-separator text-slate-300">/</span>
          <span className="header-badge">{role || 'EMPLOYEE'}</span>
        </div>
      </div>
      <div className="header-right flex items-center gap-3 md:gap-4">
        <div className="user-profile-menu flex items-center gap-2.5">
          <div className="user-avatar" title={displayName}>
            {getInitials()}
          </div>
          <div className="user-text-info hidden sm:flex flex-col">
            <span className="user-name text-xs md:text-sm font-semibold text-slate-800 leading-tight">
              {displayName}
            </span>
            {user?.email && (
              <span className="user-email text-[11px] text-slate-500 truncate max-w-[140px] md:max-w-xs">
                {user.email}
              </span>
            )}
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={logout}
          className="logout-header-btn text-xs px-2.5 py-1.5"
          title="Sign out of your session"
        >
          <IconLogout size={14} className="mr-1" />
          <span className="hidden sm:inline">Logout</span>
        </Button>
      </div>
    </header>
  );
}
