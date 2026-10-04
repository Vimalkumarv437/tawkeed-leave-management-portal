import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getRoleDashboardPath } from '../../utils/roleUtils';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import ErrorMessage from '../../components/common/ErrorMessage';
import { IconLogo } from '../../components/common/Icons';
import { extractErrorMessage } from '../../utils/errorUtils';

export default function Login(): React.ReactElement {
  const navigate = useNavigate();
  const { login, isAuthenticated, role } = useAuth();
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  if (isAuthenticated && role) {
    return <Navigate to={getRoleDashboardPath(role)} replace />;
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const profile = await login({ email, password });
      const targetPath = getRoleDashboardPath(profile.role);
      navigate(targetPath, { replace: true });
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Invalid email or password.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page-container">
      <div className="login-card">
        <div className="login-brand">
          <div className="brand-logo">
            <IconLogo size={28} className="text-white" />
          </div>
          <h2 className="brand-title">Tawkeed Investments</h2>
          <p className="brand-subtitle">Leave Management Portal</p>
        </div>
        <form onSubmit={handleSubmit} className="login-form">
          <ErrorMessage message={error} onDismiss={() => setError('')} />
          <Input
            label="Email Address"
            name="email"
            type="email"
            value={email}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
            required
            placeholder="name@tawkeed.com"
            disabled={loading}
          />
          <Input
            label="Password"
            name="password"
            type="password"
            value={password}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
            required
            placeholder="Enter your password"
            disabled={loading}
          />
          <Button
            type="submit"
            variant="primary"
            loading={loading}
            className="w-full mt-4"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>
      </div>
    </div>
  );
}

