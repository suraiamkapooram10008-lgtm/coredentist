// ============================================
// CoreDent PMS - Automation Types
// Types for n8n workflow automation
// ============================================

export interface AutomationWebhook {
  id: string;
  name: string;
  event: AutomationEvent;
  webhookUrl: string;
  secretToken?: string;
  isActive: boolean;
  lastTriggered?: string;
  createdAt: string;
  updatedAt: string;
}

export type AutomationEvent =
  | 'appointment_booked'
  | 'appointment_confirmed'
  | 'appointment_reminder'
  | 'appointment_completed'
  | 'appointment_cancelled'
  | 'appointment_no_show'
  | 'patient_registered'
  | 'treatment_plan_approved'
  | 'payment_received'
  | 'invoice_created'
  | 'monthly_report'
  | 'recall_reminder'
  | 'insurance_expiry'
  | 'low_inventory'
  | 'review_request';

export interface AutomationEventConfig {
  event: AutomationEvent;
  label: string;
  description: string;
  category: 'appointment' | 'patient' | 'billing' | 'reports' | 'inventory' | 'engagement';
  icon: string;
}

export const automationEventConfigs: AutomationEventConfig[] = [
  {
    event: 'appointment_booked',
    label: 'Appointment Booked',
    description: 'Triggered when a new appointment is scheduled',
    category: 'appointment',
    icon: 'calendar-plus',
  },
  {
    event: 'appointment_confirmed',
    label: 'Appointment Confirmed',
    description: 'Triggered when patient confirms their appointment',
    category: 'appointment',
    icon: 'calendar-check',
  },
  {
    event: 'appointment_reminder',
    label: 'Appointment Reminder',
    description: 'Triggered 24 hours before appointment (scheduled)',
    category: 'appointment',
    icon: 'bell',
  },
  {
    event: 'appointment_completed',
    label: 'Appointment Completed',
    description: 'Triggered when appointment is marked complete',
    category: 'appointment',
    icon: 'check-circle',
  },
  {
    event: 'appointment_cancelled',
    label: 'Appointment Cancelled',
    description: 'Triggered when appointment is cancelled',
    category: 'appointment',
    icon: 'calendar-x',
  },
  {
    event: 'appointment_no_show',
    label: 'Appointment No-Show',
    description: 'Triggered when patient misses appointment',
    category: 'appointment',
    icon: 'user-x',
  },
  {
    event: 'patient_registered',
    label: 'New Patient Registered',
    description: 'Triggered when a new patient is added',
    category: 'patient',
    icon: 'user-plus',
  },
  {
    event: 'treatment_plan_approved',
    label: 'Treatment Plan Approved',
    description: 'Triggered when patient approves treatment plan',
    category: 'patient',
    icon: 'file-check',
  },
  {
    event: 'payment_received',
    label: 'Payment Received',
    description: 'Triggered when payment is recorded',
    category: 'billing',
    icon: 'credit-card',
  },
  {
    event: 'invoice_created',
    label: 'Invoice Created',
    description: 'Triggered when a new invoice is generated',
    category: 'billing',
    icon: 'file-text',
  },
  {
    event: 'monthly_report',
    label: 'Monthly Report',
    description: 'Triggered on the 1st of each month',
    category: 'reports',
    icon: 'bar-chart',
  },
  {
    event: 'recall_reminder',
    label: 'Recall Reminder',
    description: 'Triggered when patient is due for 6-month checkup',
    category: 'engagement',
    icon: 'calendar-clock',
  },
  {
    event: 'insurance_expiry',
    label: 'Insurance Expiry Alert',
    description: 'Triggered before patient insurance coverage expires',
    category: 'patient',
    icon: 'shield-alert',
  },
  {
    event: 'low_inventory',
    label: 'Low Inventory Alert',
    description: 'Triggered when supplies fall below threshold',
    category: 'inventory',
    icon: 'package-x',
  },
  {
    event: 'review_request',
    label: 'Review Request',
    description: 'Triggered 24 hours after completed appointment',
    category: 'engagement',
    icon: 'star',
  },
];

// Payload types for each event
export interface AppointmentEventPayload {
  appointmentId: string;
  patientName: string;
  patientPhone?: string;
  patientEmail?: string;
  appointmentDate: string;
  appointmentTime: string;
  providerName: string;
  procedureType: string;
  clinicName: string;
}

export interface PatientEventPayload {
  patientId: string;
  patientName: string;
  patientPhone?: string;
  patientEmail?: string;
  clinicName: string;
}

export interface PaymentEventPayload {
  paymentId: string;
  invoiceId: string;
  patientName: string;
  patientEmail?: string;
  amount: number;
  paymentMethod: string;
  clinicName: string;
}

export interface TreatmentPlanEventPayload {
  treatmentPlanId: string;
  patientName: string;
  patientEmail?: string;
  totalAmount: number;
  procedures: string[];
  clinicName: string;
}

export interface MonthlyReportPayload {
  clinicName: string;
  reportMonth: string;
  totalAppointments: number;
  totalRevenue: number;
  newPatients: number;
  reportUrl?: string;
}

export interface RecallReminderPayload {
  patientId: string;
  patientName: string;
  patientPhone?: string;
  patientEmail?: string;
  lastVisitDate: string;
  dueDate: string;
  procedureType: string;
  clinicName: string;
}

export interface InsuranceExpiryPayload {
  patientId: string;
  patientName: string;
  patientEmail?: string;
  insuranceProvider: string;
  expiryDate: string;
  daysUntilExpiry: number;
  clinicName: string;
}

export interface LowInventoryPayload {
  itemId: string;
  itemName: string;
  currentQuantity: number;
  thresholdQuantity: number;
  category: string;
  clinicName: string;
}

export interface ReviewRequestPayload {
  patientId: string;
  patientName: string;
  patientEmail?: string;
  appointmentDate: string;
  providerName: string;
  reviewLink?: string;
  clinicName: string;
}

export type AutomationPayload =
  | AppointmentEventPayload
  | PatientEventPayload
  | PaymentEventPayload
  | TreatmentPlanEventPayload
  | MonthlyReportPayload
  | RecallReminderPayload
  | InsuranceExpiryPayload
  | LowInventoryPayload
  | ReviewRequestPayload;
