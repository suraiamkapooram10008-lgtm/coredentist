import { apiClient } from './api';
import type { 
  PatientRecord, 
  PatientListItem, 
  PatientFormData, 
  PatientSearchParams,
  PatientNote,
  PatientAttachment,
  MedicalHistory,
  DentalHistory,
  AppointmentStats,
} from '@/types/patient';
import type { AppointmentStatus, PaginatedResponse } from '@/types/api';

type PatientAppointmentHistoryItem = {
  id: string;
  date: string;
  type: string;
  provider: string;
  status: AppointmentStatus;
};

/**
 * Patient API service for managing patient records, notes, attachments, and appointment history.
 * Provides CRUD operations and specialized queries for patient data.
 */
export const patientApi = {
  /**
   * Retrieves a paginated list of patients with optional filtering and search parameters.
   * @param params - Search and pagination parameters
   * @returns Paginated patient list with metadata
   */
  getPatients: async (params?: PatientSearchParams): Promise<PaginatedResponse<PatientListItem>> => {
    const response = await apiClient.get<PaginatedResponse<PatientListItem>>(
      '/patients',
      params as unknown as Record<string, unknown>
    );
    if (response.success && response.data) {
      return response.data;
    }
    return {
      data: [],
      total: 0,
      page: params?.page ?? 1,
      limit: params?.limit ?? 10,
      totalPages: 0,
    };
  },

  /**
   * Retrieves a single patient record by ID.
   * @param id - Patient ID
   * @returns Patient record or null if not found
   */
  getPatient: async (id: string): Promise<PatientRecord | null> => {
    const response = await apiClient.get<PatientRecord>(`/patients/${id}`);
    return response.success ? response.data ?? null : null;
  },

  /**
   * Creates a new patient record.
   * @param data - Patient form data
   * @returns Created patient record
   * @throws Error if creation fails
   */
  createPatient: async (data: PatientFormData): Promise<PatientRecord> => {
    const response = await apiClient.post<PatientRecord>('/patients', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create patient');
  },

  /**
   * Updates an existing patient record.
   * @param id - Patient ID
   * @param data - Partial patient data to update
   * @returns Updated patient record or null if not found
   */
  updatePatient: async (id: string, data: Partial<PatientFormData>): Promise<PatientRecord | null> => {
    const response = await apiClient.put<PatientRecord>(`/patients/${id}`, data);
    return response.success ? response.data ?? null : null;
  },

  /**
   * Updates patient status (active/inactive).
   * @param id - Patient ID
   * @param status - New status
   */
  updatePatientStatus: async (id: string, status: 'active' | 'inactive'): Promise<void> => {
    await apiClient.put<void>(`/patients/${id}/status`, { status });
  },

  /**
   * Adds a note to a patient record.
   * @param patientId - Patient ID
   * @param note - Note data (without id and timestamps)
   * @returns Created note with metadata
   * @throws Error if note creation fails
   */
  addNote: async (patientId: string, note: Omit<PatientNote, 'id' | 'createdAt'>): Promise<PatientNote> => {
    const response = await apiClient.post<PatientNote>(`/patients/${patientId}/notes`, note);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to add note');
  },

  /**
   * Deletes a note from a patient record.
   * @param patientId - Patient ID
   * @param noteId - Note ID to delete
   */
  deleteNote: async (patientId: string, noteId: string): Promise<void> => {
    await apiClient.delete<void>(`/patients/${patientId}/notes/${noteId}`);
  },

  /**
   * Uploads a file attachment to a patient record.
   * @param patientId - Patient ID
   * @param file - File to upload
   * @param category - Attachment category (e.g., 'xray', 'document')
   * @returns Created attachment metadata
   * @throws Error if upload fails
   */
  uploadAttachment: async (
    patientId: string, 
    file: File, 
    category: PatientAttachment['category']
  ): Promise<PatientAttachment> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    const response = await apiClient.post<PatientAttachment>(`/patients/${patientId}/attachments`, formData);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to upload attachment');
  },

  /**
   * Deletes an attachment from a patient record.
   * @param patientId - Patient ID
   * @param attachmentId - Attachment ID to delete
   */
  deleteAttachment: async (patientId: string, attachmentId: string): Promise<void> => {
    await apiClient.delete<void>(`/patients/${patientId}/attachments/${attachmentId}`);
  },

  /**
   * Retrieves appointment history for a patient.
   * @param patientId - Patient ID
   * @returns Array of appointment history items
   */
  getAppointmentHistory: async (patientId: string): Promise<PatientAppointmentHistoryItem[]> => {
    const response = await apiClient.get<PatientAppointmentHistoryItem[]>(
      `/patients/${patientId}/appointments`
    );
    return response.success && response.data ? response.data : [];
  },
};
