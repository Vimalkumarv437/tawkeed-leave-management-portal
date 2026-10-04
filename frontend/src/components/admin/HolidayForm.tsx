import React, { useState, useEffect } from 'react';
import Input from '../common/Input';
import Button from '../common/Button';
import ErrorMessage from '../common/ErrorMessage';
import { PublicHoliday } from '../../types/admin';

export interface HolidayFormProps {
  holiday?: PublicHoliday | null;
  onSubmit: (payload: { holiday_date: string; name: string; description?: string }) => void;
  loading?: boolean;
  error?: string;
}

export default function HolidayForm({
  holiday = null,
  onSubmit,
  loading = false,
  error = '',
}: HolidayFormProps): React.ReactElement {
  const isEditing = !!holiday;
  const [formData, setFormData] = useState<{
    holiday_date: string;
    name: string;
    description: string;
  }>({
    holiday_date: '',
    name: '',
    description: '',
  });

  useEffect(() => {
    if (holiday) {
      setFormData({
        holiday_date: holiday.holiday_date || '',
        name: holiday.name || '',
        description: holiday.description || '',
      });
    }
  }, [holiday]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ): void => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    onSubmit({
      ...formData,
      description: formData.description || undefined,
    });
  };

  return (
    <form className="holiday-form" onSubmit={handleSubmit}>
      <ErrorMessage message={error} />
      <Input
        label="Holiday Date"
        name="holiday_date"
        type="date"
        value={formData.holiday_date}
        onChange={handleChange}
        required
      />
      <Input
        label="Holiday Name"
        name="name"
        value={formData.name}
        onChange={handleChange}
        required
      />
      <div className="form-group">
        <label htmlFor="description" className="form-label">
          Description (Optional)
        </label>
        <textarea
          id="description"
          name="description"
          rows={2}
          value={formData.description}
          onChange={handleChange}
          className="form-textarea"
        />
      </div>
      <div className="form-actions">
        <Button type="submit" variant="primary" loading={loading}>
          {isEditing ? 'Update Holiday' : 'Create Holiday'}
        </Button>
      </div>
    </form>
  );
}
