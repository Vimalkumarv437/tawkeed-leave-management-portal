import React, { useState } from 'react';
import Input from '../common/Input';
import Select from '../common/Select';
import Button from '../common/Button';
import ErrorMessage from '../common/ErrorMessage';
import { HALF_DAY_TYPE } from '../../utils/constants';
import { LeaveType, CreateLeavePayload, HalfDayType } from '../../types/leave';

export interface LeaveFormProps {
  leaveTypes?: LeaveType[];
  onSubmit: (payload: CreateLeavePayload) => void;
  loading?: boolean;
  error?: string;
}

export default function LeaveForm({
  leaveTypes = [],
  onSubmit,
  loading = false,
  error = '',
}: LeaveFormProps): React.ReactElement {
  const [formData, setFormData] = useState<{
    leave_type_id: string;
    start_date: string;
    end_date: string;
    start_half_day: HalfDayType;
    end_half_day: HalfDayType;
    reason: string;
  }>({
    leave_type_id: '',
    start_date: '',
    end_date: '',
    start_half_day: HALF_DAY_TYPE.NONE as HalfDayType,
    end_half_day: HALF_DAY_TYPE.NONE as HalfDayType,
    reason: '',
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ): void => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    onSubmit({
      ...formData,
      leave_type_id: parseInt(formData.leave_type_id, 10),
    });
  };

  return (
    <form className="leave-form-card" onSubmit={handleSubmit}>
      <ErrorMessage message={error} />
      <Select
        label="Leave Type"
        name="leave_type_id"
        value={formData.leave_type_id}
        onChange={handleChange}
        options={leaveTypes.map((lt) => ({ value: lt.id, label: lt.name }))}
        required
      />
      <div className="form-row-2">
        <Input
          label="Start Date"
          name="start_date"
          type="date"
          value={formData.start_date}
          onChange={handleChange}
          required
        />
        <Input
          label="End Date"
          name="end_date"
          type="date"
          value={formData.end_date}
          onChange={handleChange}
          required
        />
      </div>
      <div className="form-row-2">
        <Select
          label="Start Day Option"
          name="start_half_day"
          value={formData.start_half_day}
          onChange={handleChange}
          options={[
            { value: HALF_DAY_TYPE.NONE, label: 'Full Day' },
            { value: HALF_DAY_TYPE.FIRST_HALF, label: 'First Half' },
            { value: HALF_DAY_TYPE.SECOND_HALF, label: 'Second Half' },
          ]}
        />
        <Select
          label="End Day Option"
          name="end_half_day"
          value={formData.end_half_day}
          onChange={handleChange}
          options={[
            { value: HALF_DAY_TYPE.NONE, label: 'Full Day' },
            { value: HALF_DAY_TYPE.FIRST_HALF, label: 'First Half' },
            { value: HALF_DAY_TYPE.SECOND_HALF, label: 'Second Half' },
          ]}
        />
      </div>
      <div className="form-group">
        <label htmlFor="reason" className="form-label">
          Reason (Optional)
        </label>
        <textarea
          id="reason"
          name="reason"
          rows={3}
          value={formData.reason}
          onChange={handleChange}
          className="form-textarea"
          maxLength={2000}
        />
      </div>
      <div className="form-actions">
        <Button type="submit" variant="primary" loading={loading}>
          Submit Leave Request
        </Button>
      </div>
    </form>
  );
}
