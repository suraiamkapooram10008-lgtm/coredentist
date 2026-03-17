// ============================================
// CoreDent PMS - Patient API Service
// API calls for patient management
// ============================================

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


// Patient API service
export const patientApi = {
  // Get paginated patient list
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

  // Get single patient by ID
  getPatient: async (id: string): Promise<PatientRecord | null> => {
    const response = await apiClient.get<PatientRecord>(`/patients/${id}`);
    return response.success ? response.data ?? null : null;
  },

  // Create new patient
  createPatient: async (data: PatientFormData): Promise<PatientRecord> => {
    const response = await apiClient.post<PatientRecord>('/patients', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create patient');
  },

  // Update patient
  updatePatient: async (id: string, data: Partial<PatientFormData>): Promise<PatientRecord | null> => {
    const response = await apiClient.put<PatientRecord>(`/patients/${id}`, data);
    return response.success ? response.data ?? null : null;
  },

  // Update patient status
  updatePatientStatus: async (id: string, status: 'active' | 'inactive'): Promise<void> => {
    await apiClient.put<void>(`/patients/${id}/status`, { status });
  },

  // Add note to patient
  addNote: async (patientId: string, note: Omit<PatientNote, 'id' | 'createdAt'>): Promise<PatientNote> => {
    const response = await apiClient.post<PatientNote>(`/patients/${patientId}/notes`, note);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to add note');
  },

  // Delete note
  deleteNote: async (patientId: string, noteId: string): Promise<void> => {
    await apiClient.delete<void>(`/patients/${patientId}/notes/${noteId}`);
  },

  // Upload attachment (placeholder - needs Cloud storage)
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

  // Delete attachment
  deleteAttachment: async (patientId: string, attachmentId: string): Promise<void> => {
    await apiClient.delete<void>(`/patients/${patientId}/attachments/${attachmentId}`);
  },

  // Get patient appointment history
  getAppointmentHistory: async (patientId: string): Promise<PatientAppointmentHistoryItem[]> => {
    const response = await apiClient.get<PatientAppointmentHistoryItem[]>(
      `/patients/${patientId}/appointments`
    );
    return response.success && response.data ? response.data : [];
  },
};
