import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { getRoleDashboardPath } from '../utils/roleUtils';
import Button from '../components/common/Button';

export default function NotFound(): React.ReactElement {
  const navigate = useNavigate();
  const { role, isAuthenticated } = useAuth();

  const handleHomeRedirect = (): void => {
    if (isAuthenticated && role) {
      navigate(getRoleDashboardPath(role));
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="not-found-container">
      <div className="not-found-content">
        <h1 className="not-found-code">404</h1>
        <h2 className="not-found-title">Page Not Found</h2>
        <p className="not-found-message">
          The requested page does not exist or you do not have permission to view it.
        </p>
        <Button variant="primary" onClick={handleHomeRedirect}>
          Return to Portal
        </Button>
      </div>
    </div>
  );
}
