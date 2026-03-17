// ============================================
// CoreDent PMS - Staff Management Types
// Types for staff/user management features
// ============================================

import type { UserRole } from './api';

export interface StaffMember {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  status: StaffStatus;
  phone?: string;
  avatarUrl?: string;
  lastLoginAt?: string;
  createdAt: string;
  updatedAt: string;
}

export type StaffStatus = 'active' | 'inactive' | 'pending';

export interface StaffInvitation {
  id: string;
  email: string;
  role: UserRole;
  invitedBy: string;
  invitedByName: string;
  status: InvitationStatus;
  expiresAt: string;
  createdAt: string;
}

export type InvitationStatus = 'pending' | 'accepted' | 'expired' | 'cancelled';

export interface InviteStaffRequest {
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
}

export interface UpdateStaffRequest {
  firstName?: string;
  lastName?: string;
  role?: UserRole;
  status?: StaffStatus;
  phone?: string;
}

// Role permissions for UI visibility
export const rolePermissions: Record<UserRole, {
  label: string;
  description: string;
  color: string;
  permissions: string[];
}> = {
  owner: {
    label: 'Owner',
    description: 'Full access to all features including reports and analytics',
    color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    permissions: [
      'View all reports',
      'Access analytics',
      'Manage staff',
      'Configure practice settings',
      'View billing',
      'Full clinical access',
    ],
  },
  admin: {
    label: 'Admin',
    description: 'Clinic setup, user management, and permissions',
    color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    permissions: [
      'Manage staff',
      'Configure practice settings',
      'View billing',
      'Full clinical access',
      'Manage appointments',
    ],
  },
  dentist: {
    label: 'Dentist',
    description: 'Clinical features and view-only billing access',
    color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    permissions: [
      'View and update dental charts',
      'Create clinical notes',
      'Manage treatment plans',
      'View appointments',
      'View billing (read-only)',
    ],
  },
  front_desk: {
    label: 'Front Desk',
    description: 'Appointments, patients, and billing management',
    color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    permissions: [
      'Manage appointments',
      'Manage patients',
      'Process billing',
      'Check-in patients',
    ],
  },
};
