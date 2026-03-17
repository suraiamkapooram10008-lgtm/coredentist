// ============================================
// CoreDent PMS - Scheduling API Service
// API calls for appointment scheduling
// ============================================

import { apiClient } from './api';
import type { ScheduleAppointment, AppointmentFormData, PatientSearchResult, ScheduleProvider } from '@/types/scheduling';
import type { Chair, AppointmentTypeConfig } from '@/types/clinic';

// Scheduling API service
export const schedulingApi = {
  // Get appointments for a date range
  getAppointments: async (startDate: Date, endDate: Date): Promise<ScheduleAppointment[]> => {
    const response = await apiClient.get<ScheduleAppointment[]>('/appointments', {
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString(),
    });
    return response.success && response.data ? response.data : [];
  },

  // Get single appointment by ID
  getAppointment: async (id: string): Promise<ScheduleAppointment | null> => {
    const response = await apiClient.get<ScheduleAppointment>(`/appointments/${id}`);
    return response.success ? response.data ?? null : null;
  },

  // Create new appointment
  createAppointment: async (data: AppointmentFormData): Promise<ScheduleAppointment> => {
    const response = await apiClient.post<ScheduleAppointment>('/appointments', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create appointment');
  },

  // Update existing appointment
  updateAppointment: async (id: string, data: Partial<AppointmentFormData>): Promise<ScheduleAppointment | null> => {
    const response = await apiClient.put<ScheduleAppointment>(`/appointments/${id}`, data);
    return response.success ? response.data ?? null : null;
  },

  // Update appointment status
  updateStatus: async (id: string, status: string): Promise<void> => {
    await apiClient.put<void>(`/appointments/${id}/status`, { status });
  },

  // Cancel appointment
  cancelAppointment: async (id: string, reason?: string): Promise<void> => {
    await apiClient.post<void>(`/appointments/${id}/cancel`, { reason });
  },

  // Reschedule appointment (drag-and-drop)
  rescheduleAppointment: async (
    id: string, 
    newChairId: string, 
    newStartTime: Date
  ): Promise<ScheduleAppointment | null> => {
    const response = await apiClient.put<ScheduleAppointment>(`/appointments/${id}/reschedule`, {
      chairId: newChairId,
      startTime: newStartTime.toISOString(),
    });
    return response.success ? response.data ?? null : null;
  },

  // Get providers/dentists
  getProviders: async (): Promise<ScheduleProvider[]> => {
    const response = await apiClient.get<ScheduleProvider[]>('/providers');
    return response.success && response.data ? response.data : [];
  },

  // Get chairs/operatories
  getChairs: async (): Promise<Chair[]> => {
    const response = await apiClient.get<Chair[]>('/chairs');
    return response.success && response.data
      ? response.data.filter(c => c.isActive)
      : [];
  },

  // Get appointment types
  getAppointmentTypes: async (): Promise<AppointmentTypeConfig[]> => {
    const response = await apiClient.get<AppointmentTypeConfig[]>('/appointment-types');
    return response.success && response.data
      ? response.data.filter(t => t.isActive)
      : [];
  },

  // Search patients
  searchPatients: async (query: string): Promise<PatientSearchResult[]> => {
    if (!query.trim()) return [];
    const response = await apiClient.get<PatientSearchResult[]>('/patients/search', { query });
    return response.success && response.data ? response.data : [];
  },
};
