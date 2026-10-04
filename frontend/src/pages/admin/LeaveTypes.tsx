import React, { useState, useEffect } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import LeaveTypeTable from '../../components/admin/LeaveTypeTable';
import LeaveTypeForm from '../../components/admin/LeaveTypeForm';
import Button from '../../components/common/Button';
import Modal from '../../components/common/Modal';
import ConfirmDialog from '../../components/common/ConfirmDialog';
import ErrorMessage from '../../components/common/ErrorMessage';
import { useToast } from '../../context/ToastContext';
import { adminService } from '../../services/adminService';
import { extractErrorMessage } from '../../utils/errorUtils';
import { LeaveType } from '../../types/leave';

export default function LeaveTypes(): React.ReactElement {
  const toast = useToast();
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingType, setEditingType] = useState<LeaveType | null>(null);
  const [deletingType, setDeletingType] = useState<LeaveType | null>(null);
  const [formSubmitting, setFormSubmitting] = useState<boolean>(false);
  const [deleteLoading, setDeleteLoading] = useState<boolean>(false);

  const fetchLeaveTypes = async (): Promise<void> => {
    setLoading(true);
    setError('');
    try {
      const data = await adminService.getLeaveTypes();
      const items = (data as { items?: LeaveType[] }).items || (Array.isArray(data) ? data : []);
      setLeaveTypes(items);
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaveTypes();
  }, []);

  const handleCreateOrUpdate = async (formData: {
    name: string;
    code: string;
    default_annual_allowance: number;
  }): Promise<void> => {
    setFormSubmitting(true);
    setError('');
    try {
      if (editingType) {
        await adminService.updateLeaveType(editingType.id, formData);
        toast.success(`Leave type "${formData.name}" updated successfully.`);
      } else {
        await adminService.createLeaveType(formData);
        toast.success(`Leave type "${formData.name}" created successfully.`);
      }
      setIsModalOpen(false);
      setEditingType(null);
      fetchLeaveTypes();
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleDeleteConfirm = async (): Promise<void> => {
    if (!deletingType) return;
    setDeleteLoading(true);
    try {
      await adminService.deleteLeaveType(deletingType.id);
      toast.success(`Leave type "${deletingType.name}" deleted successfully.`);
      setDeletingType(null);
      fetchLeaveTypes();
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Leave Types & Policies"
        subtitle="Configure annual leave allowances and category rules"
        action={
          <Button
            variant="primary"
            onClick={() => {
              setEditingType(null);
              setIsModalOpen(true);
            }}
          >
            + Create Leave Type
          </Button>
        }
      />
      <ErrorMessage message={error} onDismiss={() => setError('')} />
      <LeaveTypeTable
        leaveTypes={leaveTypes}
        loading={loading}
        onEdit={(type) => {
          setEditingType(type);
          setIsModalOpen(true);
        }}
        onDelete={(type) => setDeletingType(type)}
      />

      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingType(null);
        }}
        title={editingType ? 'Edit Leave Type' : 'Create Leave Type'}
        size="md"
      >
        <LeaveTypeForm
          leaveType={editingType}
          onSubmit={handleCreateOrUpdate}
          loading={formSubmitting}
        />
      </Modal>

      {deletingType && (
        <ConfirmDialog
          isOpen={!!deletingType}
          onClose={() => setDeletingType(null)}
          onConfirm={handleDeleteConfirm}
          title="Delete Leave Type"
          message={`Are you sure you want to delete leave type "${deletingType.name}" (${deletingType.code})?`}
          confirmText="Delete"
          loading={deleteLoading}
        />
      )}
    </div>
  );
}
