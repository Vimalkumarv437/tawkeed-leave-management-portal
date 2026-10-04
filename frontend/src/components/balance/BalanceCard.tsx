import React from 'react';
import { IconWallet } from '../common/Icons';

export interface BalanceCardProps {
  title: string;
  code?: string;
  allocated?: number | string;
  used?: number | string;
  reserved?: number | string;
  remaining?: number | string;
  icon?: React.ReactNode;
  showProgress?: boolean;
}

export default function BalanceCard({
  title,
  code,
  allocated = 0,
  used = 0,
  reserved = 0,
  remaining = 0,
  icon,
  showProgress = true,
}: BalanceCardProps): React.ReactElement {
  const numAllocated = Number(allocated) || 0;
  const numUsed = Number(used) || 0;
  const numReserved = Number(reserved) || 0;
  const numRemaining =
    remaining !== undefined
      ? Number(remaining)
      : Math.max(0, numAllocated - numUsed - numReserved);

  const usedPercent =
    numAllocated > 0 ? Math.min(100, Math.max(0, (numUsed / numAllocated) * 100)) : 0;
  const reservedPercent =
    numAllocated > 0
      ? Math.min(100 - usedPercent, Math.max(0, (numReserved / numAllocated) * 100))
      : 0;

  const formatDays = (val: number): string => {
    return Number.isInteger(val) ? val.toString() : val.toFixed(1);
  };

  return (
    <div className="balance-card">
      <div className="balance-card-header">
        <div className="balance-card-title-group">
          <span className="balance-icon">{icon || <IconWallet size={18} className="text-blue-600" />}</span>
          <div>
            <h4 className="balance-title">{title}</h4>
            {code && <span className="balance-code">{code}</span>}
          </div>
        </div>
      </div>

      <div className="balance-main-stat">
        <span className="remaining-number">{formatDays(numRemaining)}</span>
        <span className="remaining-label">days available</span>
      </div>

      {showProgress && numAllocated > 0 && (
        <div
          className="balance-progress-container"
          title={`Used: ${formatDays(numUsed)}d, Pending: ${formatDays(numReserved)}d, Allocated: ${formatDays(numAllocated)}d`}
        >
          <div className="balance-progress-bar">
            <div
              className="progress-segment progress-used"
              style={{ width: `${usedPercent}%` }}
            />
            <div
              className="progress-segment progress-reserved"
              style={{ width: `${reservedPercent}%` }}
            />
          </div>
        </div>
      )}

      <div className="balance-breakdown-row">
        <div className="breakdown-item">
          <span className="breakdown-label">Allocated</span>
          <span className="breakdown-val">{formatDays(numAllocated)}d</span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">Used</span>
          <span className="breakdown-val text-muted">{formatDays(numUsed)}d</span>
        </div>
        <div className="breakdown-item">
          <span className="breakdown-label">Pending</span>
          <span className="breakdown-val text-warning">{formatDays(numReserved)}d</span>
        </div>
      </div>
    </div>
  );
}

