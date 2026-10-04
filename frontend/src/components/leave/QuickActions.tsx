import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  IconCalendarPlus,
  IconCalendar,
  IconWallet,
  IconArrowRight,
} from '../common/Icons';

export interface QuickActionItem {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  path: string;
  variant?: 'primary' | 'default';
}

export default function QuickActions(): React.ReactElement {
  const navigate = useNavigate();

  const actions: QuickActionItem[] = [
    {
      id: 'apply',
      title: 'Apply for Leave',
      description: 'Submit a new leave request for manager review',
      icon: <IconCalendarPlus size={20} className="text-indigo-600" />,
      path: '/employee/leaves/apply',
      variant: 'primary',
    },
    {
      id: 'history',
      title: 'View My Leaves',
      description: 'Track the status and history of all your requests',
      icon: <IconCalendar size={20} className="text-slate-600" />,
      path: '/employee/leaves',
    },
    {
      id: 'balance',
      title: 'View Leave Balance',
      description: 'Check available annual allocations and used days',
      icon: <IconWallet size={20} className="text-slate-600" />,
      path: '/employee/balance',
    },
  ];

  return (
    <div className="quick-actions-grid">
      {actions.map((action) => (
        <button
          key={action.id}
          type="button"
          onClick={() => navigate(action.path)}
          className={`quick-action-card ${action.variant === 'primary' ? 'quick-action-primary' : ''}`}
        >
          <div className="quick-action-icon">{action.icon}</div>
          <div className="quick-action-content">
            <h4 className="quick-action-title">{action.title}</h4>
            <p className="quick-action-desc">{action.description}</p>
          </div>
          <span className="quick-action-arrow">
            <IconArrowRight size={16} />
          </span>
        </button>
      ))}
    </div>
  );
}

