import React, { ReactNode } from 'react';
import { IconInbox } from './Icons';

export interface EmptyStateProps {
  title?: string;
  message?: string;
  action?: ReactNode;
  icon?: ReactNode;
}

export default function EmptyState({
  title = 'No Data Available',
  message = 'There are no records to display at this time.',
  action = null,
  icon = null,
}: EmptyStateProps) {
  return (
    <div className="empty-state-container">
      <div className="empty-state-icon">
        {icon || <IconInbox size={36} className="text-slate-400" />}
      </div>
      <h4 className="empty-state-title">{title}</h4>
      <p className="empty-state-message">{message}</p>
      {action && <div className="empty-state-action">{action}</div>}
    </div>
  );
}
