/**
 * Appointments API Service
 * Appointment management with React Query integration
 */

import { apiClient } from './api';
import type { ApiResponse } from '@/types/api';

// ============================================
// Types
// ============================================

export interface Appointment {
  id: string;
  patient: string;
  patientName: string;
  time: string;
  duration: string;
  type: string;
  dentist: string;
  status: 'Confirmed' | 'Pending' | 'Cancelled' | 'Completed';
  date?: string;
  notes?: string;
}

export interface AppointmentStats {
  todayAppointments: number;
  confirmed: number;
  pending: number;
  cancelled: number;
}

export interface AppointmentType {
  id: string;
  name: string;
  duration: number;
  description?: string;
}

export interface AppointmentListParams {
  date?: string;
  status?: string;
  search?: string;
  page?: number;
  limit?: number;
}

// ============================================
// API Functions
// ============================================

/**
 * List appointments with optional filters
 */
export const listAppointments = async (
  params?: AppointmentListParams
): Promise<ApiResponse<{ appointments: Appointment[]; total: number }>> => {
  const queryParams = new URLSearchParams();
  if (params?.date) queryParams.append('date', params.date);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.search) queryParams.append('search', params.search);
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  return apiClient.get<{ appointments: Appointment[]; total: number }>(`/appointments?${queryParams}`);
};

/**
 * Get appointment by ID
 */
export const getAppointment = async (
  id: string
): Promise<ApiResponse<Appointment>> => {
  return apiClient.get<Appointment>(`/appointments/${id}`);
};

/**
 * Create a new appointment
 */
export const createAppointment = async (
  data: Omit<Appointment, 'id'>
): Promise<ApiResponse<Appointment>> => {
  return apiClient.post<Appointment>('/appointments', data);
};

/**
 * Update an appointment
 */
export const updateAppointment = async (
  id: string,
  data: Partial<Appointment>
): Promise<ApiResponse<Appointment>> => {
  return apiClient.put<Appointment>(`/appointments/${id}`, data);
};

/**
 * Delete an appointment
 */
export const deleteAppointment = async (
  id: string
): Promise<ApiResponse<void>> => {
  return apiClient.delete<void>(`/appointments/${id}`);
};

/**
 * Get appointment statistics
 */
export const getAppointmentStats = async (): Promise<ApiResponse<AppointmentStats>> => {
  return apiClient.get<AppointmentStats>('/appointments/stats');
};

/**
 * List appointment types
 */
export const listAppointmentTypes = async (): Promise<ApiResponse<{ types: AppointmentType[] }>> => {
  return apiClient.get<{ types: AppointmentType[] }>('/appointments/types');
};

/**
 * Send appointment reminder
 */
export const sendAppointmentReminder = async (
  id: string
): Promise<ApiResponse<{ message: string }>> => {
  return apiClient.post<{ message: string }>(`/appointments/${id}/reminder`, {});
};