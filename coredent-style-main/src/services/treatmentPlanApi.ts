// ============================================
// CoreDent PMS - Treatment Plan API Service
// API calls for treatment plan operations
// ============================================

import type { 
  TreatmentPlan, 
  TreatmentProcedure, 
  TreatmentStatus,
  ProcedurePhase 
} from '@/types/treatmentPlan';
import { apiClient } from './api';

export const treatmentPlanApi = {
  // Get all treatment plans
  async getPlans(patientId?: string): Promise<TreatmentPlan[]> {
    const endpoint = patientId ? `/patients/${patientId}/treatment-plans` : '/treatment-plans';
    const response = await apiClient.get<TreatmentPlan[]>(endpoint);
    return response.success && response.data ? response.data : [];
  },

  // Get single treatment plan
  async getPlan(planId: string): Promise<TreatmentPlan | null> {
    const response = await apiClient.get<TreatmentPlan>(`/treatment-plans/${planId}`);
    return response.success ? response.data ?? null : null;
  },

  // Create treatment plan
  async createPlan(plan: Omit<TreatmentPlan, 'id' | 'createdAt' | 'updatedAt'>): Promise<TreatmentPlan> {
    const response = await apiClient.post<TreatmentPlan>('/treatment-plans', plan);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create treatment plan');
  },

  // Update treatment plan
  async updatePlan(planId: string, updates: Partial<TreatmentPlan>): Promise<TreatmentPlan> {
    const response = await apiClient.put<TreatmentPlan>(`/treatment-plans/${planId}`, updates);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update treatment plan');
  },

  // Update plan status
  async updatePlanStatus(planId: string, status: TreatmentStatus): Promise<TreatmentPlan> {
    const response = await apiClient.put<TreatmentPlan>(`/treatment-plans/${planId}/status`, { status });
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update treatment plan status');
  },

  // Add procedure to plan
  async addProcedure(planId: string, procedure: Omit<TreatmentProcedure, 'id'>): Promise<TreatmentProcedure> {
    const response = await apiClient.post<TreatmentProcedure>(`/treatment-plans/${planId}/procedures`, procedure);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to add procedure');
  },

  // Update procedure
  async updateProcedure(
    planId: string, 
    procedureId: string, 
    updates: Partial<TreatmentProcedure>
  ): Promise<TreatmentProcedure> {
    const response = await apiClient.put<TreatmentProcedure>(
      `/treatment-plans/${planId}/procedures/${procedureId}`,
      updates
    );
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update procedure');
  },

  // Mark procedure as completed
  async completeProcedure(
    planId: string, 
    procedureId: string, 
    actualCost?: number
  ): Promise<TreatmentProcedure> {
    const response = await apiClient.post<TreatmentProcedure>(
      `/treatment-plans/${planId}/procedures/${procedureId}/complete`,
      { actualCost }
    );
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to complete procedure');
  },

  // Delete procedure
  async deleteProcedure(planId: string, procedureId: string): Promise<void> {
    await apiClient.delete<void>(`/treatment-plans/${planId}/procedures/${procedureId}`);
  },

  // Delete plan
  async deletePlan(planId: string): Promise<void> {
    await apiClient.delete<void>(`/treatment-plans/${planId}`);
  },
};
