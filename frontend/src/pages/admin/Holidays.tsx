import React, { useState, useEffect } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import HolidayTable from '../../components/admin/HolidayTable';
import HolidayForm from '../../components/admin/HolidayForm';
import Button from '../../components/common/Button';
import Modal from '../../components/common/Modal';
import ConfirmDialog from '../../components/common/ConfirmDialog';
import ErrorMessage from '../../components/common/ErrorMessage';
import { useToast } from '../../context/ToastContext';
import { adminService } from '../../services/adminService';
import { extractErrorMessage } from '../../utils/errorUtils';
import { PublicHoliday } from '../../types/admin';

export default function Holidays(): React.ReactElement {
  const toast = useToast();
  const [holidays, setHolidays] = useState<PublicHoliday[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingHoliday, setEditingHoliday] = useState<PublicHoliday | null>(null);
  const [deletingHoliday, setDeletingHoliday] = useState<PublicHoliday | null>(null);
  const [formSubmitting, setFormSubmitting] = useState<boolean>(false);

  const fetchHolidays = async (): Promise<void> => {
    setLoading(true);
    setError('');
    try {
      const data = await adminService.getHolidays();
      const items = (data as { items?: PublicHoliday[] }).items || (Array.isArray(data) ? data : []);
      setHolidays(items);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHolidays();
  }, []);

  const handleCreateOrUpdate = async (formData: { holiday_date: string; name: string; description?: string }): Promise<void> => {
    setFormSubmitting(true);
    setError('');
    try {
      if (editingHoliday) {
        await adminService.updateHoliday(editingHoliday.id, formData);
        toast.success(`Holiday "${formData.name}" updated successfully.`);
      } else {
        await adminService.createHoliday(formData);
        toast.success(`Holiday "${formData.name}" added successfully.`);
      }
      setIsModalOpen(false);
      setEditingHoliday(null);
      fetchHolidays();
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleDeleteConfirm = async (): Promise<void> => {
    if (!deletingHoliday) return;
    try {
      await adminService.deleteHoliday(deletingHoliday.id);
      toast.success(`Holiday "${deletingHoliday.name}" deleted successfully.`);
      setDeletingHoliday(null);
      fetchHolidays();
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      setError(msg);
      toast.error(msg);
    }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Public Holidays"
        subtitle="Manage official company holidays excluded from leave calculations"
        action={
          <Button
            variant="primary"
            onClick={() => {
              setEditingHoliday(null);
              setIsModalOpen(true);
            }}
          >
            + Add Holiday
          </Button>
        }
      />
      <ErrorMessage message={error} onDismiss={() => setError('')} />
      <HolidayTable
        holidays={holidays}
        loading={loading}
        onEdit={(holiday) => {
          setEditingHoliday(holiday);
          setIsModalOpen(true);
        }}
        onDelete={(holiday) => setDeletingHoliday(holiday)}
      />

      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingHoliday(null);
        }}
        title={editingHoliday ? 'Edit Public Holiday' : 'Add Public Holiday'}
        size="md"
      >
        <HolidayForm
          holiday={editingHoliday}
          onSubmit={handleCreateOrUpdate}
          loading={formSubmitting}
        />
      </Modal>

      {deletingHoliday && (
        <ConfirmDialog
          isOpen={!!deletingHoliday}
          onClose={() => setDeletingHoliday(null)}
          onConfirm={handleDeleteConfirm}
          title="Delete Holiday"
          message={`Are you sure you want to delete "${deletingHoliday.name}"?`}
          confirmText="Delete"
        />
      )}
    </div>
  );
}
