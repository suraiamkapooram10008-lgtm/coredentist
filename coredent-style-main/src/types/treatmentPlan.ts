export type TreatmentStatus = 'proposed' | 'accepted' | 'in_progress' | 'completed' | 'cancelled';
export type ProcedurePhase = 'phase_1' | 'phase_2' | 'phase_3' | 'phase_4';

export interface TreatmentProcedure {
  id: string;
  procedureCode: string;
  procedureName: string;
  status: 'planned' | 'completed';
  toothNumber?: number;
  phase: ProcedurePhase;
  estimatedCost: number;
  notes?: string;
  dentistId: string;
  dentistName: string;
}

export interface TreatmentPlan {
  id: string;
  title: string;
  description?: string;
  patientId: string;
  patientName: string;
  status: TreatmentStatus;
  notes?: string;
  procedures: TreatmentProcedure[];
  createdBy: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface PlanSummary {
  totalEstimatedCost: number;
  totalInsuranceEstimate: number;
  totalPatientResponsibility: number;
  totalCompleted: number;
  totalPlanned: number;
}

export function calculatePlanSummary(plan: TreatmentPlan): PlanSummary {
  const totalEstimatedCost = plan.procedures.reduce((sum, p) => sum + p.estimatedCost, 0);
  // Simulate 60% insurance coverage for demonstration
  const totalInsuranceEstimate = Math.round(totalEstimatedCost * 0.6);
  const totalPatientResponsibility = totalEstimatedCost - totalInsuranceEstimate;

  const totalCompleted = plan.procedures
    .filter((p) => p.status === 'completed')
    .reduce((sum, p) => sum + p.estimatedCost, 0);

  const totalPlanned = plan.procedures
    .filter((p) => p.status === 'planned')
    .reduce((sum, p) => sum + p.estimatedCost, 0);

  return {
    totalEstimatedCost,
    totalInsuranceEstimate,
    totalPatientResponsibility,
    totalCompleted,
    totalPlanned,
  };
}
