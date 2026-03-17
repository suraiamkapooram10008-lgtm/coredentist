// ============================================
// CoreDent PMS - Insurance Types
// TypeScript types for insurance management
// ============================================

export type InsuranceType = 'primary' | 'secondary' | 'tertiary';
export type ClaimStatus = 'draft' | 'submitted' | 'accepted' | 'rejected' | 'paid' | 'partial';
export type PreAuthStatus = 'pending' | 'approved' | 'denied' | 'expired';
export type RelationshipToInsured = 'self' | 'spouse' | 'child' | 'other';

export interface InsuranceCarrier {
  id: string;
  name: string;
  phone: string;
  email?: string;
  address?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  payerId?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface PatientInsurance {
  id: string;
  patientId: string;
  patientName?: string;
  carrierId: string;
  carrierName?: string;
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
  isActive: boolean;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface InsuranceClaim {
  id: string;
  patientId: string;
  patientName?: string;
  insuranceId: string;
  carrierName?: string;
  claimNumber?: string;
  serviceDate: string;
  submissionDate?: string;
  status: ClaimStatus;
  totalAmount: number;
  approvedAmount?: number;
  paidAmount?: number;
  patientResponsibility?: number;
  procedures: ClaimProcedure[];
  notes?: string;
  rejectionReason?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ClaimProcedure {
  id: string;
  procedureCode: string;
  description: string;
  toothNumber?: string;
  quantity: number;
  chargedAmount: number;
  approvedAmount?: number;
  paidAmount?: number;
}

export interface InsurancePreAuthorization {
  id: string;
  patientId: string;
  patientName?: string;
  insuranceId: string;
  carrierName?: string;
  authNumber?: string;
  requestDate: string;
  expirationDate?: string;
  status: PreAuthStatus;
  requestedProcedures: string[];
  approvedProcedures?: string[];
  estimatedCost?: number;
  approvedAmount?: number;
  notes?: string;
  denialReason?: string;
  createdAt: string;
  updatedAt: string;
}

export interface InsuranceSummary {
  totalClaims: number;
  pendingClaims: number;
  approvedClaims: number;
  rejectedClaims: number;
  totalBilled: number;
  totalApproved: number;
  totalPaid: number;
  activePreAuths: number;
}
