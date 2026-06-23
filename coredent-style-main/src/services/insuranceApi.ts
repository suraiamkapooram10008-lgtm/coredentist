// ============================================
// CoreDent PMS - Insurance API Service
// API calls for insurance management
// ============================================

import type {
  InsuranceCarrier,
  PatientInsurance,
  InsuranceClaim,
  InsurancePreAuthorization,
  InsuranceSummary,
  ClaimStatus,
  PreAuthStatus,
  InsuranceType,
  RelationshipToInsured,
} from '@/types/insurance';
import { apiClient } from './api';
import { requireApiData, requireApiSuccess } from './apiResponse';

export const insuranceApi = {
  // ============================================
  // Insurance Carriers
  // ============================================

  async getCarriers(filters?: { search?: string; isActive?: boolean }): Promise<InsuranceCarrier[]> {
    return requireApiData(
      await apiClient.get<{ carriers: InsuranceCarrier[]; count: number }>('/insurance/carriers', filters as Record<string, unknown>),
      'Failed to load insurance carriers',
    ).carriers;
  },

  async getCarrier(carrierId: string): Promise<InsuranceCarrier | null> {
    return requireApiData(
      await apiClient.get<InsuranceCarrier>(`/insurance/carriers/${carrierId}`),
      'Failed to load insurance carrier',
    );
  },

  async createCarrier(data: Omit<InsuranceCarrier, 'id' | 'createdAt' | 'updatedAt'>): Promise<InsuranceCarrier> {
    const response = await apiClient.post<InsuranceCarrier>('/insurance/carriers', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create carrier');
  },

  async updateCarrier(carrierId: string, data: Partial<InsuranceCarrier>): Promise<InsuranceCarrier> {
    const response = await apiClient.put<InsuranceCarrier>(`/insurance/carriers/${carrierId}`, data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update carrier');
  },

  async deleteCarrier(carrierId: string): Promise<void> {
    requireApiSuccess(
      await apiClient.delete<void>(`/insurance/carriers/${carrierId}`),
      'Failed to delete insurance carrier',
    );
  },

  // ============================================
  // Patient Insurance
  // ============================================

  async getPatientInsurance(patientId: string): Promise<PatientInsurance[]> {
    return requireApiData(
      await apiClient.get<{ insurances: PatientInsurance[]; count: number }>(`/insurance/patients/${patientId}/policies`),
      'Failed to load patient insurance',
    ).insurances;
  },

  async getInsurancePolicy(policyId: string): Promise<PatientInsurance | null> {
    return requireApiData(
      await apiClient.get<PatientInsurance>(`/insurance/policies/${policyId}`),
      'Failed to load insurance policy',
    );
  },

  async addPatientInsurance(patientId: string, data: {
    carrierId: string;
    insuranceType: InsuranceType;
    policyNumber: string;
    groupNumber?: string;
    subscriberName: string;
    subscriberId: string;
    relationshipToInsured: RelationshipToInsured;
    effectiveDate: string;
    expirationDate?: string;
    coveragePercent?: number;
    annualMaximum?: number;
    deductible?: number;
    deductibleMet?: number;
    notes?: string;
  }): Promise<PatientInsurance> {
    const response = await apiClient.post<PatientInsurance>(`/insurance/patients/${patientId}/policies`, data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to add insurance');
  },

  async updateInsurancePolicy(policyId: string, data: Partial<PatientInsurance>): Promise<PatientInsurance> {
    const response = await apiClient.put<PatientInsurance>(`/insurance/policies/${policyId}`, data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update insurance');
  },

  async deleteInsurancePolicy(policyId: string): Promise<void> {
    requireApiSuccess(
      await apiClient.delete<void>(`/insurance/policies/${policyId}`),
      'Failed to delete insurance policy',
    );
  },

  // ============================================
  // Insurance Claims
  // ============================================

  async getClaims(filters?: {
    patientId?: string;
    status?: ClaimStatus;
    startDate?: string;
    endDate?: string;
  }): Promise<InsuranceClaim[]> {
    return requireApiData(
      await apiClient.get<{ claims: InsuranceClaim[]; count: number }>('/insurance/claims', filters as Record<string, unknown>),
      'Failed to load insurance claims',
    ).claims;
  },

  async getClaim(claimId: string): Promise<InsuranceClaim | null> {
    return requireApiData(
      await apiClient.get<InsuranceClaim>(`/insurance/claims/${claimId}`),
      'Failed to load insurance claim',
    );
  },

  async createClaim(data: {
    patientId: string;
    insuranceId: string;
    serviceDate: string;
    procedures: {
      procedureCode: string;
      description: string;
      toothNumber?: string;
      quantity: number;
      chargedAmount: number;
    }[];
    notes?: string;
  }): Promise<InsuranceClaim> {
    const response = await apiClient.post<InsuranceClaim>('/insurance/claims', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create claim');
  },

  async updateClaim(claimId: string, data: Partial<InsuranceClaim>): Promise<InsuranceClaim> {
    const response = await apiClient.put<InsuranceClaim>(`/insurance/claims/${claimId}`, data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update claim');
  },

  async submitClaim(claimId: string): Promise<InsuranceClaim> {
    const response = await apiClient.post<InsuranceClaim>(`/insurance/claims/${claimId}/submit`, {});
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to submit claim');
  },

  async deleteClaim(claimId: string): Promise<void> {
    requireApiSuccess(
      await apiClient.delete<void>(`/insurance/claims/${claimId}`),
      'Failed to delete insurance claim',
    );
  },

  // ============================================
  // Pre-Authorizations
  // ============================================

  async getPreAuthorizations(filters?: {
    patientId?: string;
    status?: PreAuthStatus;
  }): Promise<InsurancePreAuthorization[]> {
    return requireApiData(
      await apiClient.get<{ pre_authorizations: InsurancePreAuthorization[]; count: number }>('/insurance/pre-auth', filters as Record<string, unknown>),
      'Failed to load insurance pre-authorizations',
    ).pre_authorizations;
  },

  async getPreAuthorization(preAuthId: string): Promise<InsurancePreAuthorization | null> {
    return requireApiData(
      await apiClient.get<InsurancePreAuthorization>(`/insurance/pre-auth/${preAuthId}`),
      'Failed to load insurance pre-authorization',
    );
  },

  async createPreAuthorization(data: {
    patientId: string;
    insuranceId: string;
    requestedProcedures: string[];
    estimatedCost?: number;
    notes?: string;
  }): Promise<InsurancePreAuthorization> {
    const response = await apiClient.post<InsurancePreAuthorization>('/insurance/pre-auth', data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to create pre-authorization');
  },

  async updatePreAuthorization(preAuthId: string, data: Partial<InsurancePreAuthorization>): Promise<InsurancePreAuthorization> {
    const response = await apiClient.put<InsurancePreAuthorization>(`/insurance/pre-auth/${preAuthId}`, data);
    if (response.success && response.data) {
      return response.data;
    }
    throw new Error(response.error?.message || 'Failed to update pre-authorization');
  },

  async deletePreAuthorization(preAuthId: string): Promise<void> {
    requireApiSuccess(
      await apiClient.delete<void>(`/insurance/pre-auth/${preAuthId}`),
      'Failed to delete insurance pre-authorization',
    );
  },

  // ============================================
  // Summary & Reports
  // ============================================

  async getSummary(): Promise<InsuranceSummary> {
    return requireApiData(
      await apiClient.get<InsuranceSummary>('/insurance/summary'),
      'Failed to load insurance summary',
    );
  },
};
