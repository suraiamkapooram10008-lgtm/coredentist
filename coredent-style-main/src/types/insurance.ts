// ============================================
// CoreDent PMS - Insurance Type Definitions
// ============================================

export type ClaimStatus =
  | 'draft'
  | 'submitted'
  | 'accepted'
  | 'rejected'
  | 'paid'
  | 'partial'
  | 'appealed';

export type PreAuthStatus =
  | 'pending'
  | 'approved'
  | 'denied'
  | 'expired';

export type InsuranceType = 'primary' | 'secondary' | 'tertiary';

export type RelationshipToInsured =
  | 'self'
  | 'spouse'
  | 'child'
  | 'other';

export interface InsuranceCarrier {
  id: string;
  name: string;
  payerId?: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  website?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface PatientInsurance {
  id: string;
  patientId: string;
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
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ClaimProcedure {
  procedureCode: string;
  description: string;
  toothNumber?: string;
  quantity: number;
  chargedAmount: number;
  allowedAmount?: number;
  paidAmount?: number;
}

export interface InsuranceClaim {
  id: string;
  patientId: string;
  patientName: string;
  insuranceId: string;
  carrierName?: string;
  claimNumber: string;
  status: ClaimStatus;
  serviceDate: string;
  submittedDate?: string;
  processedDate?: string;
  procedures: ClaimProcedure[];
  totalAmount: number;
  approvedAmount?: number;
  paidAmount?: number;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface InsurancePreAuthorization {
  id: string;
  patientId: string;
  patientName?: string;
  insuranceId: string;
  carrierName?: string;
  authNumber?: string;
  status: PreAuthStatus;
  requestedProcedures: string[];
  estimatedCost?: number;
  approvedCost?: number;
  requestDate: string;
  expirationDate?: string;
  notes?: string;
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
