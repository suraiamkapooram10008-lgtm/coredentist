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

export const insuranceApi = {
  // ============================================
  // Insurance Carriers
  // ============================================

  async getCarriers(filters?: { search?: string; isActive?: boolean }): Promise<InsuranceCarrier[]> {
    const response = await apiClient.get<InsuranceCarrier[]>('/insurance/carriers', filters as Record<string, unknown>);
    return response.success && response.data ? response.data : [];
  },

  async getCarrier(carrierId: string): Promise<InsuranceCarrier | null> {
    const response = await apiClient.get<InsuranceCarrier>(`/insurance/carriers/${carrierId}`);
    return response.success ? response.data ?? null : null;
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
    await apiClient.delete<void>(`/insurance/carriers/${carrierId}`);
  },

  // ============================================
  // Patient Insurance
  // ============================================

  async getPatientInsurance(patientId: string): Promise<PatientInsurance[]> {
    const response = await apiClient.get<PatientInsurance[]>(`/insurance/patients/${patientId}/policies`);
    return response.success && response.data ? response.data : [];
  },

  async getInsurancePolicy(policyId: string): Promise<PatientInsurance | null> {
    const response = await apiClient.get<PatientInsurance>(`/insurance/policies/${policyId}`);
    return response.success ? response.data ?? null : null;
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
    await apiClient.delete<void>(`/insurance/policies/${policyId}`);
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
    const response = await apiClient.get<InsuranceClaim[]>('/insurance/claims', filters as Record<string, unknown>);
    return response.success && response.data ? response.data : [];
  },

  async getClaim(claimId: string): Promise<InsuranceClaim | null> {
    const response = await apiClient.get<InsuranceClaim>(`/insurance/claims/${claimId}`);
    return response.success ? response.data ?? null : null;
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
    await apiClient.delete<void>(`/insurance/claims/${claimId}`);
  },

  // ============================================
  // Pre-Authorizations
  // ============================================

  async getPreAuthorizations(filters?: {
    patientId?: string;
    status?: PreAuthStatus;
  }): Promise<InsurancePreAuthorization[]> {
    const response = await apiClient.get<InsurancePreAuthorization[]>('/insurance/pre-auth', filters as Record<string, unknown>);
    return response.success && response.data ? response.data : [];
  },

  async getPreAuthorization(preAuthId: string): Promise<InsurancePreAuthorization | null> {
    const response = await apiClient.get<InsurancePreAuthorization>(`/insurance/pre-auth/${preAuthId}`);
    return response.success ? response.data ?? null : null;
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
    await apiClient.delete<void>(`/insurance/pre-auth/${preAuthId}`);
  },

  // ============================================
  // Summary & Reports
  // ============================================

  async getSummary(): Promise<InsuranceSummary> {
    const response = await apiClient.get<InsuranceSummary>('/insurance/summary');
    if (response.success && response.data) {
      return response.data;
    }
    return {
      totalClaims: 0,
      pendingClaims: 0,
      approvedClaims: 0,
      rejectedClaims: 0,
      totalBilled: 0,
      totalApproved: 0,
      totalPaid: 0,
      activePreAuths: 0,
    };
  },
};
