export interface TreatmentPlan {
  id: string;
  title: string;
  description?: string;
  patientId: string;
  patientName: string;
  notes?: string;
}
