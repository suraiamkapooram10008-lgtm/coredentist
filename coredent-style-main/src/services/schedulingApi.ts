import { apiClient } from './api';
import type { ScheduleAppointment, AppointmentFormData, PatientSearchResult, ScheduleProvider } from '@/types/scheduling';
import type { Chair, AppointmentTypeConfig } from '@/types/clinic';

/**
 * Scheduling API service for managing appointments, providers, and clinic resources.
 * Handles appointment CRUD operations, rescheduling, and availability queries.
 */
export const schedulingApi = {
  /**
   * Retrieves appointments within a date range.
   * @param startDate - Start of date range
   * @param endDate - End of date range
   * @returns Array of appointments in the specified range
   */
  getAppointments: async (startDate: Date, endDate: Date): Promise<ScheduleAppointment[]> => {
    const response = await apiClient.get<ScheduleAppointment[]>('/appointments', {
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString(),
    });
    return response.success && response.data ? response.data : [];
  },

  /**
   * Retrieves a single appointment by ID.
   * @param id - Appointment ID
   * @returns Appointment details or null if not found
   */
  getAppointment: async (id: string): Promise<ScheduleAppointment | null> => {
    const response = await apiClient.get<ScheduleAppointment>(`/appointments/${id}`);
    return response.success ? response.data ?? null : null;
  },

  /**
   * Creates a new appointment.
   * @param data - Appointment form data
   * @returns Created appointment with ID and timestamps
   * @throws Error if creation fails
   */
  createAppointment: async (data: AppointmentFormData): Promise<ScheduleAppointment> => {
    const response = await apiClient.post<ScheduleAppointment>('/appointments', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create appointment');
  },

  /**
   * Updates an existing appointment.
   * @param id - Appointment ID
   * @param data - Partial appointment data to update
   * @returns Updated appointment or null if not found
   */
  updateAppointment: async (id: string, data: Partial<AppointmentFormData>): Promise<ScheduleAppointment | null> => {
    const response = await apiClient.put<ScheduleAppointment>(`/appointments/${id}`, data);
    return response.success ? response.data ?? null : null;
  },

  /**
   * Updates appointment status (e.g., confirmed, completed, no-show).
   * @param id - Appointment ID
   * @param status - New appointment status
   */
  updateStatus: async (id: string, status: string): Promise<void> => {
    await apiClient.put<void>(`/appointments/${id}/status`, { status });
  },

  /**
   * Cancels an appointment with optional reason.
   * @param id - Appointment ID
   * @param reason - Optional cancellation reason
   */
  cancelAppointment: async (id: string, reason?: string): Promise<void> => {
    await apiClient.post<void>(`/appointments/${id}/cancel`, { reason });
  },

  /**
   * Reschedules an appointment to a different time/chair (supports drag-and-drop).
   * @param id - Appointment ID
   * @param newChairId - New chair/operatory ID
   * @param newStartTime - New appointment start time
   * @returns Updated appointment or null if not found
   */
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

  /**
   * Retrieves all available providers/dentists.
   * @returns Array of provider information
   */
  getProviders: async (): Promise<ScheduleProvider[]> => {
    const response = await apiClient.get<ScheduleProvider[]>('/providers');
    return response.success && response.data ? response.data : [];
  },

  /**
   * Retrieves all active chairs/operatories.
   * @returns Array of active chair information
   */
  getChairs: async (): Promise<Chair[]> => {
    const response = await apiClient.get<Chair[]>('/chairs');
    return response.success && response.data
      ? response.data.filter(c => c.isActive)
      : [];
  },

  /**
   * Retrieves all active appointment types.
   * @returns Array of active appointment type configurations
   */
  getAppointmentTypes: async (): Promise<AppointmentTypeConfig[]> => {
    const response = await apiClient.get<AppointmentTypeConfig[]>('/appointment-types');
    return response.success && response.data
      ? response.data.filter(t => t.isActive)
      : [];
  },

  /**
   * Searches for patients by name or ID.
   * @param query - Search query string
   * @returns Array of matching patient results
   */
  searchPatients: async (query: string): Promise<PatientSearchResult[]> => {
    if (!query.trim()) return [];
    const response = await apiClient.get<PatientSearchResult[]>('/patients/search', { query });
    return response.success && response.data ? response.data : [];
  },
};
