import React from 'react';

export interface ErrorMessageProps {
  message?: string | null;
  onDismiss?: (() => void) | null;
  className?: string;
}

export default function ErrorMessage({
  message,
  onDismiss = null,
  className = '',
}: ErrorMessageProps) {
  if (!message) return null;

  return (
    <div className={`alert-banner alert-danger ${className}`}>
      <span className="alert-icon">⚠️</span>
      <div className="alert-content">{message}</div>
      {onDismiss && (
        <button type="button" className="alert-dismiss" onClick={onDismiss}>
          &times;
        </button>
      )}
    </div>
  );
}
