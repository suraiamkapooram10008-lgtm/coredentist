export type AutomationEvent =
  | 'appointment_booked'
  | 'appointment_cancelled'
  | 'appointment_completed'
  | 'appointment_confirmed'
  | 'appointment_no_show'
  | 'patient_created'
  | 'patient_registered'
  | 'invoice_created'
  | 'invoice_overdue'
  | 'payment_received'
  | 'review_request'
  | 'treatment_plan_approved'
  | 'treatment_plan_created';

export interface AutomationWebhook {
  id: string;
  name: string;
  url: string;
  event: AutomationEvent;
  isActive: boolean;
  secretToken?: string;
  createdAt?: string;
  updatedAt?: string;
}

export type AutomationPayload = Record<string, any>;
