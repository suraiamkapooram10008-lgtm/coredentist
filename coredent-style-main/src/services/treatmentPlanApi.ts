import { apiClient } from "./api";
import { requireApiData, requireApiSuccess } from "./apiResponse";
import type { TreatmentPlan, TreatmentProcedure } from "@/types/treatmentPlan";

export const treatmentPlanApi = {
  getPlans: async (): Promise<TreatmentPlan[]> =>
    requireApiData(
      await apiClient.get<TreatmentPlan[]>("/treatment-plans"),
      "Failed to load treatment plans",
    ),

  getPlan: async (id: string): Promise<TreatmentPlan | null> =>
    requireApiData(
      await apiClient.get<TreatmentPlan>(`/treatment-plans/${id}`),
      "Failed to load treatment plan",
    ),

  createPlan: async (
    plan: Omit<TreatmentPlan, "id" | "createdAt" | "updatedAt">,
  ): Promise<TreatmentPlan> =>
    requireApiData(
      await apiClient.post<TreatmentPlan>("/treatment-plans", plan),
      "Failed to create treatment plan",
    ),

  updatePlan: async (
    id: string,
    plan: Partial<TreatmentPlan>,
  ): Promise<TreatmentPlan> =>
    requireApiData(
      await apiClient.put<TreatmentPlan>(`/treatment-plans/${id}`, plan),
      "Failed to update treatment plan",
    ),

  deletePlan: async (id: string): Promise<void> => {
    requireApiSuccess(
      await apiClient.delete<void>(`/treatment-plans/${id}`),
      "Failed to delete treatment plan",
    );
  },

  addProcedure: async (
    planId: string,
    procedure: Omit<TreatmentProcedure, "id">,
  ): Promise<TreatmentProcedure> =>
    requireApiData(
      await apiClient.post<TreatmentProcedure>(
        `/treatment-plans/${planId}/procedures`,
        procedure,
      ),
      "Failed to add treatment procedure",
    ),

  completeProcedure: async (
    planId: string,
    procedureId: string,
  ): Promise<TreatmentProcedure> =>
    requireApiData(
      await apiClient.put<TreatmentProcedure>(
        `/treatment-plans/${planId}/procedures/${procedureId}/complete`,
      ),
      "Failed to complete treatment procedure",
    ),

  deleteProcedure: async (
    planId: string,
    procedureId: string,
  ): Promise<void> => {
    requireApiSuccess(
      await apiClient.delete<void>(
        `/treatment-plans/${planId}/procedures/${procedureId}`,
      ),
      "Failed to delete treatment procedure",
    );
  },
};