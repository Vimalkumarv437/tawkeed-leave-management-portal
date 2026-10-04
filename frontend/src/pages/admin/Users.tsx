import React, { useState, useEffect } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import UserTable from '../../components/admin/UserTable';
import UserForm from '../../components/admin/UserForm';
import Button from '../../components/common/Button';
import Modal from '../../components/common/Modal';
import ErrorMessage from '../../components/common/ErrorMessage';
import { useToast } from '../../context/ToastContext';
import { adminService } from '../../services/adminService';
import { ROLES } from '../../utils/constants';
import { extractErrorMessage } from '../../utils/errorUtils';
import { User, UserCreatePayload, UserUpdatePayload } from '../../types/auth';

export default function Users(): React.ReactElement {
  const toast = useToast();
  const [users, setUsers] = useState<User[]>([]);
  const [managers, setManagers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formSubmitting, setFormSubmitting] = useState<boolean>(false);

  const fetchUsers = async (): Promise<void> => {
    setLoading(true);
    setError('');
    try {
      const data = await adminService.getUsers({ limit: 100 });
      const userList = Array.isArray(data) ? data : (data as { items?: User[] }).items || [];
      setUsers(userList);
      setManagers(userList.filter((u: User) => u.role === ROLES.MANAGER && u.is_active));
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateOrUpdate = async (formData: UserCreatePayload | UserUpdatePayload): Promise<void> => {
    setFormSubmitting(true);
    setError('');
    try {
      if (editingUser) {
        await adminService.updateUser(editingUser.id, formData as UserUpdatePayload);
        toast.success('User updated successfully.');
      } else {
        await adminService.createUser(formData as UserCreatePayload);
        toast.success('User created successfully.');
      }
      setIsModalOpen(false);
      setEditingUser(null);
      fetchUsers();
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleToggleStatus = async (user: User): Promise<void> => {
    try {
      if (user.is_active) {
        await adminService.deactivateUser(user.id);
        toast.success(`User ${user.first_name} ${user.last_name} deactivated successfully.`);
      } else {
        await adminService.reactivateUser(user.id);
        toast.success(`User ${user.first_name} ${user.last_name} reactivated successfully.`);
      }
      fetchUsers();
    } catch (err: unknown) {
      const msg = extractErrorMessage(err);
      setError(msg);
      toast.error(msg);
    }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="User Management"
        subtitle="Manage employees, managers, and administrator accounts"
        action={
          <Button
            variant="primary"
            onClick={() => {
              setEditingUser(null);
              setError('');
              setIsModalOpen(true);
            }}
          >
            + Create User
          </Button>
        }
      />
      <ErrorMessage message={error} onDismiss={() => setError('')} />
      <UserTable
        users={users}
        loading={loading}
        onEdit={(user) => {
          setEditingUser(user);
          setError('');
          setIsModalOpen(true);
        }}
        onToggleStatus={handleToggleStatus}
      />

      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingUser(null);
          setError('');
        }}
        title={editingUser ? 'Edit User Profile' : 'Create New User'}
        subtitle={
          editingUser
            ? 'Update user account information and role permissions'
            : 'Configure profile details, role permissions, and manager assignment'
        }
        size="lg"
      >
        <UserForm
          user={editingUser}
          managers={managers}
          onSubmit={handleCreateOrUpdate}
          onCancel={() => {
            setIsModalOpen(false);
            setEditingUser(null);
            setError('');
          }}
          loading={formSubmitting}
          error={error}
        />
      </Modal>
    </div>
  );
}
