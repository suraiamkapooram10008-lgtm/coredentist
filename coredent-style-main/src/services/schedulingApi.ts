import { apiClient } from "./api";
import { requireApiData, requireApiSuccess } from "./apiResponse";
import type { AppointmentTypeConfig, Chair } from "@/types/clinic";
import type {
  AppointmentFormData,
  PatientSearchResult,
  ScheduleAppointment,
  ScheduleProvider,
} from "@/types/scheduling";

export const schedulingApi = {
  getAppointments: async (
    startDate: Date,
    endDate: Date,
  ): Promise<ScheduleAppointment[]> =>
    requireApiData(
      await apiClient.get<ScheduleAppointment[]>("/appointments", {
        startDate: startDate.toISOString(),
        endDate: endDate.toISOString(),
      }),
      "Failed to load appointments",
    ),

  getAppointment: async (id: string): Promise<ScheduleAppointment | null> =>
    requireApiData(
      await apiClient.get<ScheduleAppointment>(`/appointments/${id}`),
      "Failed to load appointment",
    ),

  createAppointment: async (
    data: AppointmentFormData,
  ): Promise<ScheduleAppointment> =>
    requireApiData(
      await apiClient.post<ScheduleAppointment>("/appointments", data),
      "Failed to create appointment",
    ),

  updateAppointment: async (
    id: string,
    data: Partial<AppointmentFormData>,
  ): Promise<ScheduleAppointment | null> =>
    requireApiData(
      await apiClient.put<ScheduleAppointment>(`/appointments/${id}`, data),
      "Failed to update appointment",
    ),

  updateStatus: async (id: string, status: string): Promise<void> => {
    requireApiSuccess(
      await apiClient.put<void>(`/appointments/${id}/status`, { status }),
      "Failed to update appointment status",
    );
  },

  cancelAppointment: async (id: string, reason?: string): Promise<void> => {
    requireApiSuccess(
      await apiClient.post<void>(`/appointments/${id}/cancel`, { reason }),
      "Failed to cancel appointment",
    );
  },

  rescheduleAppointment: async (
    id: string,
    newChairId: string,
    newStartTime: Date,
  ): Promise<ScheduleAppointment | null> =>
    requireApiData(
      await apiClient.put<ScheduleAppointment>(`/appointments/${id}/reschedule`, {
        chairId: newChairId,
        startTime: newStartTime.toISOString(),
      }),
      "Failed to reschedule appointment",
    ),

  getProviders: async (): Promise<ScheduleProvider[]> =>
    requireApiData(
      await apiClient.get<ScheduleProvider[]>("/providers"),
      "Failed to load providers",
    ),

  getChairs: async (): Promise<Chair[]> =>
    requireApiData(
      await apiClient.get<Chair[]>("/chairs"),
      "Failed to load chairs",
    ).filter((chair) => chair.isActive),

  getAppointmentTypes: async (): Promise<AppointmentTypeConfig[]> =>
    requireApiData(
      await apiClient.get<AppointmentTypeConfig[]>("/appointment-types"),
      "Failed to load appointment types",
    ).filter((type) => type.isActive),

  searchPatients: async (query: string): Promise<PatientSearchResult[]> => {
    if (!query.trim()) {
      return [];
    }

    return requireApiData(
      await apiClient.get<PatientSearchResult[]>("/patients/search", { query }),
      "Failed to search patients",
    );
  },
};