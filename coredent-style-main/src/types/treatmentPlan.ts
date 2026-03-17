// ============================================
// CoreDent PMS - Treatment Plan Types
// Types for treatment planning and tracking
// ============================================

export type TreatmentStatus = 'proposed' | 'accepted' | 'in_progress' | 'completed' | 'cancelled';
export type ProcedurePhase = 'urgent' | 'phase_1' | 'phase_2' | 'phase_3' | 'maintenance';

export interface TreatmentProcedure {
  id: string;
  procedureCode: string;
  procedureName: string;
  toothNumber?: number;
  surfaces?: string[];
  phase: ProcedurePhase;
  status: 'planned' | 'scheduled' | 'completed';
  estimatedCost: number;
  actualCost?: number;
  scheduledDate?: string;
  completedDate?: string;
  notes?: string;
  dentistId: string;
  dentistName: string;
}

export interface TreatmentPlan {
  id: string;
  patientId: string;
  patientName: string;
  title: string;
  description?: string;
  status: TreatmentStatus;
  procedures: TreatmentProcedure[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  acceptedAt?: string;
  completedAt?: string;
  notes?: string;
}

export interface TreatmentPlanSummary {
  totalProcedures: number;
  completedProcedures: number;
  totalEstimatedCost: number;
  totalActualCost: number;
  remainingCost: number;
}

// Phase display configuration
export const PHASE_CONFIG: Record<ProcedurePhase, { label: string; color: string; order: number }> = {
  urgent: { label: 'Urgent', color: 'bg-red-100 text-red-700 border-red-300', order: 0 },
  phase_1: { label: 'Phase 1', color: 'bg-blue-100 text-blue-700 border-blue-300', order: 1 },
  phase_2: { label: 'Phase 2', color: 'bg-purple-100 text-purple-700 border-purple-300', order: 2 },
  phase_3: { label: 'Phase 3', color: 'bg-amber-100 text-amber-700 border-amber-300', order: 3 },
  maintenance: { label: 'Maintenance', color: 'bg-green-100 text-green-700 border-green-300', order: 4 },
};

export const STATUS_CONFIG: Record<TreatmentStatus, { label: string; color: string }> = {
  proposed: { label: 'Proposed', color: 'bg-slate-100 text-slate-700' },
  accepted: { label: 'Accepted', color: 'bg-blue-100 text-blue-700' },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700' },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-700' },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-700' },
};

// Common procedure templates with costs
export const PROCEDURE_TEMPLATES: { code: string; name: string; defaultCost: number }[] = [
  { code: 'D0120', name: 'Periodic Oral Evaluation', defaultCost: 50 },
  { code: 'D0150', name: 'Comprehensive Oral Evaluation', defaultCost: 85 },
  { code: 'D0210', name: 'Full Mouth X-rays', defaultCost: 150 },
  { code: 'D0274', name: 'Bitewing X-rays (4 films)', defaultCost: 65 },
  { code: 'D1110', name: 'Prophylaxis (Cleaning)', defaultCost: 100 },
  { code: 'D1208', name: 'Fluoride Application', defaultCost: 35 },
  { code: 'D2140', name: 'Amalgam Filling - 1 Surface', defaultCost: 150 },
  { code: 'D2150', name: 'Amalgam Filling - 2 Surfaces', defaultCost: 200 },
  { code: 'D2330', name: 'Composite Filling - 1 Surface (Anterior)', defaultCost: 175 },
  { code: 'D2331', name: 'Composite Filling - 2 Surfaces (Anterior)', defaultCost: 225 },
  { code: 'D2391', name: 'Composite Filling - 1 Surface (Posterior)', defaultCost: 200 },
  { code: 'D2392', name: 'Composite Filling - 2 Surfaces (Posterior)', defaultCost: 275 },
  { code: 'D2740', name: 'Crown - Porcelain/Ceramic', defaultCost: 1200 },
  { code: 'D2750', name: 'Crown - Porcelain Fused to Metal', defaultCost: 1100 },
  { code: 'D2751', name: 'Crown - Full Cast Metal', defaultCost: 1000 },
  { code: 'D3310', name: 'Root Canal - Anterior', defaultCost: 800 },
  { code: 'D3320', name: 'Root Canal - Premolar', defaultCost: 950 },
  { code: 'D3330', name: 'Root Canal - Molar', defaultCost: 1200 },
  { code: 'D4341', name: 'Periodontal Scaling (per quadrant)', defaultCost: 250 },
  { code: 'D4910', name: 'Periodontal Maintenance', defaultCost: 150 },
  { code: 'D7140', name: 'Extraction - Simple', defaultCost: 175 },
  { code: 'D7210', name: 'Extraction - Surgical', defaultCost: 350 },
  { code: 'D6010', name: 'Implant - Endosteal', defaultCost: 2500 },
  { code: 'D6065', name: 'Implant Crown - Porcelain', defaultCost: 1500 },
];

export function calculatePlanSummary(plan: TreatmentPlan): TreatmentPlanSummary {
  const completedProcedures = plan.procedures.filter(p => p.status === 'completed');
  const totalEstimatedCost = plan.procedures.reduce((sum, p) => sum + p.estimatedCost, 0);
  const totalActualCost = completedProcedures.reduce((sum, p) => sum + (p.actualCost || p.estimatedCost), 0);
  const remainingCost = plan.procedures
    .filter(p => p.status !== 'completed')
    .reduce((sum, p) => sum + p.estimatedCost, 0);

  return {
    totalProcedures: plan.procedures.length,
    completedProcedures: completedProcedures.length,
    totalEstimatedCost,
    totalActualCost,
    remainingCost,
  };
}
