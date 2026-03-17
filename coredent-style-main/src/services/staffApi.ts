// ============================================
// CoreDent PMS - Staff Management API
// API service for staff/user management
// ============================================

import { apiClient } from './api';
import type { StaffMember, StaffInvitation, InviteStaffRequest, UpdateStaffRequest } from '@/types/staff';
import type { ApiResponse, PaginatedResponse } from '@/types/api';

export interface StaffListParams {
  search?: string;
  role?: string;
  status?: string;
  page?: number;
  limit?: number;
}

export const staffApi = {
  // List all staff members
  list: (params?: StaffListParams) =>
    apiClient.get<PaginatedResponse<StaffMember>>(
      '/staff',
      params as unknown as Record<string, string | number>
    ),

  // Get single staff member
  getById: (id: string) =>
    apiClient.get<StaffMember>(`/staff/${id}`),

  // Update staff member
  update: (id: string, data: UpdateStaffRequest) =>
    apiClient.put<StaffMember>(`/staff/${id}`, data),

  // Deactivate staff member
  deactivate: (id: string) =>
    apiClient.put<StaffMember>(`/staff/${id}/deactivate`),

  // Reactivate staff member
  reactivate: (id: string) =>
    apiClient.put<StaffMember>(`/staff/${id}/reactivate`),

  // Send staff invitation
  invite: (data: InviteStaffRequest) =>
    apiClient.post<StaffInvitation>('/staff/invitations', data),

  // List pending invitations
  listInvitations: () =>
    apiClient.get<StaffInvitation[]>('/staff/invitations'),

  // Resend invitation
  resendInvitation: (id: string) =>
    apiClient.post<StaffInvitation>(`/staff/invitations/${id}/resend`),

  // Cancel invitation
  cancelInvitation: (id: string) =>
    apiClient.delete<void>(`/staff/invitations/${id}`),
};
