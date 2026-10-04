import React from 'react';

export interface LoadingProps {
  message?: string;
  fullScreen?: boolean;
}

export default function Loading({
  message = 'Loading...',
  fullScreen = false,
}: LoadingProps) {
  if (fullScreen) {
    return (
      <div className="loading-fullscreen">
        <div className="spinner-lg" />
        <p className="loading-text">{message}</p>
      </div>
    );
  }

  return (
    <div className="loading-inline">
      <div className="spinner-md" />
      <p className="loading-text">{message}</p>
    </div>
  );
}
