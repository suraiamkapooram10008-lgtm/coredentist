// ============================================
// CoreDent PMS - Dental Chart API Service
// API calls for dental charting operations
// ============================================

import type { 
  DentalChart, 
  ToothData, 
  ToothProcedure,
  ToothCondition 
} from '@/types/dentalChart';
import { apiClient } from './api';

export const dentalChartApi = {
  // Get dental chart for a patient
  async getChart(patientId: string): Promise<DentalChart> {
    const response = await apiClient.get<DentalChart>(`/patients/${patientId}/chart`);
    if (response.success && response.data) {
      return response.data;
    }
    return {
      patientId,
      patientName: '',
      teeth: [],
      lastUpdated: new Date().toISOString(),
    };
  },
  
  // Update tooth condition
  async updateToothCondition(
    patientId: string,
    toothNumber: number,
    condition: ToothCondition
  ): Promise<ToothData> {
    const response = await apiClient.put<ToothData>(
      `/patients/${patientId}/chart/teeth/${toothNumber}`,
      { condition }
    );
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update tooth condition');
  },
  
  // Add procedure to tooth
  async addProcedure(
    patientId: string,
    procedure: Omit<ToothProcedure, 'id'>
  ): Promise<ToothProcedure> {
    const response = await apiClient.post<ToothProcedure>(
      `/patients/${patientId}/chart/procedures`,
      procedure
    );
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to add procedure');
  },
  
  // Update procedure status
  async updateProcedureStatus(
    patientId: string,
    procedureId: string,
    status: ToothProcedure['status']
  ): Promise<ToothProcedure> {
    const response = await apiClient.put<ToothProcedure>(
      `/patients/${patientId}/chart/procedures/${procedureId}`,
      { status }
    );
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update procedure status');
  },
  
  // Delete procedure
  async deleteProcedure(patientId: string, procedureId: string): Promise<void> {
    await apiClient.delete<void>(`/patients/${patientId}/chart/procedures/${procedureId}`);
  },
  
  // Get procedure history for a tooth
  async getToothHistory(
    patientId: string,
    toothNumber: number
  ): Promise<ToothProcedure[]> {
    const response = await apiClient.get<ToothProcedure[]>(
      `/patients/${patientId}/chart/teeth/${toothNumber}/history`
    );
    return response.success && response.data ? response.data : [];
  },
};
