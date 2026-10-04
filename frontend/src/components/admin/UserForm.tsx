import React, { useState, useEffect, useMemo } from 'react';
import Input from '../common/Input';
import Select from '../common/Select';
import Button from '../common/Button';
import ErrorMessage from '../common/ErrorMessage';
import { IconUser, IconBriefcase, IconShield } from '../common/Icons';
import { ROLES } from '../../utils/constants';
import { User, Role, UserCreatePayload, UserUpdatePayload } from '../../types/auth';

export interface UserFormProps {
  user?: User | null;
  managers?: User[];
  onSubmit: (payload: UserCreatePayload | UserUpdatePayload) => void;
  onCancel?: () => void;
  loading?: boolean;
  error?: string;
}

interface FormState {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  role: Role;
  manager_id: string;
}

const MIN_PASSWORD_LENGTH = 12;

const EMPTY_FORM: FormState = {
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  role: ROLES.EMPLOYEE as Role,
  manager_id: '',
};

const ROLE_OPTIONS: {
  role: Role;
  title: string;
  icon: React.ReactNode;
  desc: string;
  scope: string;
  selected: string;
  iconSelected: string;
}[] = [
    {
      role: ROLES.EMPLOYEE as Role,
      title: 'Employee',
      icon: <IconUser size={18} />,
      desc: 'Applies for leave and checks balances',
      scope: 'Needs a reporting manager. Can submit leave requests and view personal balances.',
      selected: 'border-blue-600 bg-blue-50 ring-2 ring-blue-500/20',
      iconSelected: 'bg-blue-600 text-white',
    },
    {
      role: ROLES.MANAGER as Role,
      title: 'Manager',
      icon: <IconBriefcase size={18} />,
      desc: 'Reviews and approves team requests',
      scope: 'Can approve or reject team leave requests. Does not need a reporting manager.',
      selected: 'border-purple-600 bg-purple-50 ring-2 ring-purple-500/20',
      iconSelected: 'bg-purple-600 text-white',
    },
    {
      role: ROLES.ADMIN as Role,
      title: 'Admin',
      icon: <IconShield size={18} />,
      desc: 'Manages users, policies and settings',
      scope: 'Full access to users, balances, leave types, company holidays and audit logs.',
      selected: 'border-amber-600 bg-amber-50 ring-2 ring-amber-500/20',
      iconSelected: 'bg-amber-600 text-white',
    },
  ];

/** Returns 0-4 based on length and character variety. */
function getPasswordStrength(pw: string): number {
  if (!pw) return 0;
  let score = 0;
  if (pw.length >= MIN_PASSWORD_LENGTH) score++;
  if (pw.length >= 16) score++;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
  if (/\d/.test(pw) && /[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

const STRENGTH_LABELS = ['Too short', 'Weak', 'Fair', 'Good', 'Strong'];
const STRENGTH_COLORS = ['bg-slate-200', 'bg-red-500', 'bg-amber-500', 'bg-lime-500', 'bg-emerald-500'];

function SectionHeading({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      {hint && <span className="text-xs text-slate-500">{hint}</span>}
    </div>
  );
}

export default function UserForm({
  user = null,
  managers = [],
  onSubmit,
  onCancel,
  loading = false,
  error = '',
}: UserFormProps): React.ReactElement {
  const isEditing = !!user;
  const [formData, setFormData] = useState<FormState>(EMPTY_FORM);
  const [validationError, setValidationError] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);

  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        password: '',
        role: user.role || (ROLES.EMPLOYEE as Role),
        manager_id: user.manager_id ? String(user.manager_id) : '',
      });
    } else {
      setFormData(EMPTY_FORM);
    }
    setValidationError('');
    setShowPassword(false);
  }, [user]);

  const activeRole = useMemo(
    () => ROLE_OPTIONS.find((r) => r.role === formData.role) ?? ROLE_OPTIONS[0],
    [formData.role]
  );

  const strength = getPasswordStrength(formData.password);
  const isEmployee = formData.role === ROLES.EMPLOYEE;

  const handleRoleSelect = (selectedRole: Role): void => {
    setValidationError('');
    setFormData((prev) => ({
      ...prev,
      role: selectedRole,
      manager_id: selectedRole === ROLES.EMPLOYEE ? prev.manager_id : '',
    }));
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>): void => {
    const { name, value } = e.target;
    setValidationError('');
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    setValidationError('');

    if (!isEditing && formData.password.length < MIN_PASSWORD_LENGTH) {
      setValidationError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters long.`);
      return;
    }
    if (isEmployee && !formData.manager_id) {
      setValidationError('Select a reporting manager for this employee.');
      return;
    }

    const { password, manager_id, ...rest } = formData;
    const payload: Record<string, unknown> = {
      ...rest,
      manager_id: isEmployee && manager_id ? parseInt(manager_id, 10) : null,
    };
    if (!isEditing || password) payload.password = password;

    onSubmit(payload as unknown as UserCreatePayload | UserUpdatePayload);
  };

  const submitLabel = isEditing ? 'Save changes' : `Create ${activeRole.title.toLowerCase()}`;

  return (
    <form className="@container flex flex-col text-slate-800" onSubmit={handleSubmit} noValidate>
      {/* Fields (the modal body is the only scroll area) */}
      <div className="flex flex-col gap-6">
        {(validationError || error) && (
          <div role="alert">
            <ErrorMessage message={validationError || error} />
          </div>
        )}

        {/* Role */}
        <section>
          <SectionHeading title="Account role" hint="Sets what this person can do" />
          <div role="radiogroup" aria-label="Account role" className="grid grid-cols-1 gap-2.5 @xl:grid-cols-3">
            {ROLE_OPTIONS.map((cfg) => {
              const isSelected = formData.role === cfg.role;
              return (
                <button
                  key={cfg.role}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  onClick={() => handleRoleSelect(cfg.role)}
                  className={`flex items-center gap-3 rounded-xl border p-3 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 @xl:flex-col @xl:items-start @xl:gap-2.5 @xl:p-4 ${isSelected ? cfg.selected : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                    }`}
                >
                  <span
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors ${isSelected ? cfg.iconSelected : 'bg-slate-100 text-slate-600'
                      }`}
                  >
                    {cfg.icon}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold text-slate-900">{cfg.title}</span>
                    <span className="mt-0.5 block text-xs leading-snug text-slate-500">{cfg.desc}</span>
                  </span>
                </button>
              );
            })}
          </div>
          <p
            className="mt-3 rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs leading-relaxed text-slate-600"
            aria-live="polite"
          >
            {activeRole.scope}
          </p>
        </section>

        {/* Personal details */}
        <section>
          <SectionHeading title="Personal details" />
          <div className="grid grid-cols-1 gap-x-4 @md:grid-cols-2">
            <Input label="First name" name="first_name" value={formData.first_name} onChange={handleChange} required autoComplete="given-name" placeholder="Enter first name" />
            <Input label="Last name" name="last_name" value={formData.last_name} onChange={handleChange} required autoComplete="family-name" placeholder="Enter last name" />
          </div>
          <Input label="Email address" name="email" type="email" value={formData.email} onChange={handleChange} required autoComplete="off" placeholder="Enter email address" />
        </section>

        {/* Password (create only) */}
        {!isEditing && (
          <section>
            <SectionHeading title="Temporary password" hint="The user resets it on first login" />
            <Input
              label="Password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleChange}
              required
              minLength={MIN_PASSWORD_LENGTH}
              autoComplete="new-password"
              placeholder={`At least ${MIN_PASSWORD_LENGTH} characters`}
            />
            <div className="mt-1 flex items-center gap-3">
              <div
                className="flex flex-1 gap-1"
                role="meter"
                aria-label="Password strength"
                aria-valuemin={0}
                aria-valuemax={4}
                aria-valuenow={strength}
                aria-valuetext={STRENGTH_LABELS[strength]}
              >
                {[1, 2, 3, 4].map((seg) => (
                  <span
                    key={seg}
                    className={`h-1.5 flex-1 rounded-full transition-colors ${strength >= seg ? STRENGTH_COLORS[strength] : 'bg-slate-200'}`}
                  />
                ))}
              </div>
              <span className="w-16 text-right text-xs text-slate-500">{formData.password ? STRENGTH_LABELS[strength] : ''}</span>
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-pressed={showPassword}
                className="rounded-md px-2 py-1 text-xs font-medium text-blue-700 hover:bg-blue-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </section>
        )}

        {/* Reporting manager (employee only) */}
        {isEmployee && (
          <section className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <SectionHeading title="Reporting manager" />
            <Select
              label="Manager"
              name="manager_id"
              value={formData.manager_id}
              onChange={handleChange}
              options={managers.map((m) => ({
                value: String(m.id),
                label: `${m.first_name} ${m.last_name} (${m.email})`,
              }))}
              placeholder="Choose a manager"
              required
            />
            <p className="mt-1.5 text-xs text-slate-500">
              {managers.length === 0
                ? 'No managers available. Create a manager account first.'
                : 'This manager reviews and approves the employee’s leave requests.'}
            </p>
          </section>
        )}
      </div>

      {/* Footer */}
      <div className="sticky bottom-0 z-10 -mx-4 -mb-4 mt-6 flex flex-col-reverse gap-2.5 border-t border-slate-200 bg-white px-4 pb-4 pt-4 sm:-mx-5 sm:-mb-5 sm:px-5 sm:pb-5 @md:flex-row @md:items-center @md:justify-end @md:gap-3">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} disabled={loading} className="w-full px-6 @md:w-auto">
            Cancel
          </Button>
        )}
        <Button type="submit" variant="primary" loading={loading} className="w-full px-6 @md:w-auto">
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}