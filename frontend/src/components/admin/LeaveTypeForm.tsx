import React, { useState, useEffect } from 'react';
import Input from '../common/Input';
import Select from '../common/Select';
import Button from '../common/Button';
import ErrorMessage from '../common/ErrorMessage';
import { LeaveType } from '../../types/leave';

const STANDARD_LEAVE_CODES = [
  { value: 'ANNUAL', label: 'ANNUAL - Annual / Vacation Leave' },
  { value: 'SICK', label: 'SICK - Sick / Medical Leave' },
  { value: 'CASUAL', label: 'CASUAL - Casual Leave' },
  { value: 'MATERNITY', label: 'MATERNITY - Maternity Leave' },
  { value: 'PATERNITY', label: 'PATERNITY - Paternity Leave' },
  { value: 'COMPENSATORY', label: 'COMPENSATORY - Compensatory Off' },
  { value: 'BEREAVEMENT', label: 'BEREAVEMENT - Bereavement Leave' },
  { value: 'UNPAID', label: 'UNPAID - Unpaid / Loss of Pay' },
  { value: 'STUDY', label: 'STUDY - Study / Exam Leave' },
  { value: 'SPECIAL', label: 'SPECIAL - Special Discretionary Leave' },
];

export interface LeaveTypeFormProps {
  leaveType?: LeaveType | null;
  onSubmit: (payload: { name: string; code: string; default_annual_allowance: number }) => void;
  loading?: boolean;
  error?: string;
}

export default function LeaveTypeForm({
  leaveType = null,
  onSubmit,
  loading = false,
  error = '',
}: LeaveTypeFormProps): React.ReactElement {
  const isEditing = !!leaveType;
  const [formData, setFormData] = useState<{
    name: string;
    code: string;
    default_annual_allowance: string | number;
  }>({
    name: '',
    code: 'ANNUAL',
    default_annual_allowance: '15',
  });

  useEffect(() => {
    if (leaveType) {
      setFormData({
        name: leaveType.name || '',
        code: leaveType.code || 'ANNUAL',
        default_annual_allowance: leaveType.default_annual_allowance ?? '',
      });
    }
  }, [leaveType]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ): void => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    onSubmit({
      name: formData.name,
      code: formData.code,
      default_annual_allowance: parseFloat(String(formData.default_annual_allowance)) || 0,
    });
  };

  return (
    <form className="leave-type-form" onSubmit={handleSubmit}>
      <ErrorMessage message={error} />
      <Input
        label="Leave Type Name"
        name="name"
        value={formData.name}
        onChange={handleChange}
        placeholder="e.g. Annual Vacation"
        required
      />
      <Select
        label="Code (Standard Classification)"
        name="code"
        value={formData.code}
        onChange={handleChange}
        options={STANDARD_LEAVE_CODES}
        required
        disabled={isEditing}
      />
      <Input
        label="Default Annual Allowance (Days)"
        name="default_annual_allowance"
        type="number"
        step="0.5"
        min="0"
        value={formData.default_annual_allowance}
        onChange={handleChange}
        required
      />
      <div className="form-actions mt-4">
        <Button type="submit" variant="primary" loading={loading}>
          {isEditing ? 'Update Leave Type' : 'Create Leave Type'}
        </Button>
      </div>
    </form>
  );
}
