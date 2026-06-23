import { apiClient } from "./api";
import { requireApiData, requireApiSuccess } from "./apiResponse";
import type {
  PatientAttachment,
  PatientFormData,
  PatientListItem,
  PatientNote,
  PatientRecord,
  PatientSearchParams,
} from "@/types/patient";
import type { AppointmentStatus, PaginatedResponse } from "@/types/api";

type PatientAppointmentHistoryItem = {
  id: string;
  date: string;
  type: string;
  provider: string;
  status: AppointmentStatus;
};

export const patientApi = {
  getPatients: async (
    params?: PatientSearchParams,
  ): Promise<PaginatedResponse<PatientListItem>> =>
    requireApiData(
      await apiClient.get<PaginatedResponse<PatientListItem>>(
        "/patients",
        params as unknown as Record<string, unknown>,
      ),
      "Failed to load patients",
    ),

  getPatient: async (id: string): Promise<PatientRecord | null> =>
    requireApiData(
      await apiClient.get<PatientRecord>(`/patients/${id}`),
      "Failed to load patient",
    ),

  createPatient: async (data: PatientFormData): Promise<PatientRecord> =>
    requireApiData(
      await apiClient.post<PatientRecord>("/patients", data),
      "Failed to create patient",
    ),

  updatePatient: async (
    id: string,
    data: Partial<PatientFormData>,
  ): Promise<PatientRecord | null> =>
    requireApiData(
      await apiClient.put<PatientRecord>(`/patients/${id}`, data),
      "Failed to update patient",
    ),

  updatePatientStatus: async (
    id: string,
    status: "active" | "inactive",
  ): Promise<void> => {
    requireApiSuccess(
      await apiClient.put<void>(`/patients/${id}/status`, { status }),
      "Failed to update patient status",
    );
  },

  addNote: async (
    patientId: string,
    note: Omit<PatientNote, "id" | "createdAt">,
  ): Promise<PatientNote> =>
    requireApiData(
      await apiClient.post<PatientNote>(`/patients/${patientId}/notes`, note),
      "Failed to add note",
    ),

  deleteNote: async (patientId: string, noteId: string): Promise<void> => {
    requireApiSuccess(
      await apiClient.delete<void>(`/patients/${patientId}/notes/${noteId}`),
      "Failed to delete note",
    );
  },

  uploadAttachment: async (
    patientId: string,
    file: File,
    category: PatientAttachment["category"],
  ): Promise<PatientAttachment> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", category);
    return requireApiData(
      await apiClient.post<PatientAttachment>(
        `/patients/${patientId}/attachments`,
        formData,
      ),
      "Failed to upload attachment",
    );
  },

  deleteAttachment: async (
    patientId: string,
    attachmentId: string,
  ): Promise<void> => {
    requireApiSuccess(
      await apiClient.delete<void>(
        `/patients/${patientId}/attachments/${attachmentId}`,
      ),
      "Failed to delete attachment",
    );
  },

  getAppointmentHistory: async (
    patientId: string,
  ): Promise<PatientAppointmentHistoryItem[]> =>
    requireApiData(
      await apiClient.get<PatientAppointmentHistoryItem[]>(
        `/patients/${patientId}/appointments`,
      ),
      "Failed to load patient appointment history",
    ),
};