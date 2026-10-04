import React, { useState } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import ErrorMessage from '../../components/common/ErrorMessage';

/**
 * ChangePassword Component
 *
 * NOTE - BACKEND GAP:
 * The current FastAPI backend does not yet provide a self-service password change
 * or first-login reset endpoint (e.g. POST /api/auth/change-password).
 * This page informs the user and administrator of the required backend capability.
 */
export default function ChangePassword(): React.ReactElement {
  const [currentPassword, setCurrentPassword] = useState<string>('');
  const [newPassword, setNewPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [backendGapMessage, setBackendGapMessage] = useState<string>(
    'Notice: The backend does not currently have an active /api/auth/change-password endpoint. Please contact your system administrator to update account credentials.'
  );

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    setBackendGapMessage(
      'Unable to submit: Self-service password change endpoint is not currently implemented in the backend API.'
    );
  };

  return (
    <div className="change-password-container">
      <PageHeader
        title="Change Password"
        subtitle="Update your portal access credentials"
      />
      <div className="card-container max-w-md">
        <ErrorMessage message={backendGapMessage} />
        <form onSubmit={handleSubmit}>
          <Input
            label="Current / Temporary Password"
            name="currentPassword"
            type="password"
            value={currentPassword}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCurrentPassword(e.target.value)}
            disabled
          />
          <Input
            label="New Password"
            name="newPassword"
            type="password"
            value={newPassword}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)}
            disabled
          />
          <Input
            label="Confirm New Password"
            name="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}
            disabled
          />
          <Button type="submit" variant="primary" disabled className="w-full mt-4">
            Update Password (Backend Endpoint Pending)
          </Button>
        </form>
      </div>
    </div>
  );
}
