import React from 'react';

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  className?: string;
}

export default function PageHeader({
  title,
  subtitle = '',
  action = null,
  className = '',
}: PageHeaderProps): React.ReactElement {
  return (
    <div className={`page-header flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 ${className}`}>
      <div className="page-header-text">
        <h1 className="page-title text-xl md:text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
        {subtitle && <p className="page-subtitle text-xs md:text-sm text-slate-500 mt-1">{subtitle}</p>}
      </div>
      {action && <div className="page-header-action flex items-center gap-2.5 shrink-0 flex-wrap">{action}</div>}
    </div>
  );
}
