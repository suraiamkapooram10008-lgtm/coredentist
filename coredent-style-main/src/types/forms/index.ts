/**
 * Form Type Definitions
 * Centralized types for all form data structures
 */

// ============================================
// Payment Forms
// ============================================

/**
 * Razorpay order creation request
 * Used when initiating a payment order with Razorpay
 */
export interface RazorpayOrderCreate {
  invoice_id: string;
  amount: number;
  currency: 'INR' | 'USD';
  receipt: string;
  description?: string;
  customer_id?: string;
  notes?: Record<string, string>;
}

/**
 * Razorpay payment verification request
 * Used to verify a completed payment transaction
 */
export interface RazorpayPaymentVerify {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
  invoice_id: string;
}

/**
 * Razorpay payment response from checkout
 * Returned by Razorpay checkout handler
 */
export interface RazorpayPaymentResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

// ============================================
// Booking Forms
// ============================================

/**
 * Public booking page configuration
 * Defines the appearance and behavior of a public booking page
 */
export interface BookingPage {
  page_slug: string;
  page_title: string;
  welcome_message?: string;
  logo_url?: string;
  primary_color?: string;
  background_image_url?: string;
  allow_new_patients: boolean;
  allow_existing_patients: boolean;
  booking_window_days: number;
  min_notice_hours: number;
  business_hours: Record<string, unknown>;
  intake_form_fields: Array<Record<string, unknown>>;
}

/**
 * Public booking form data
 * Collected from patients during online booking
 */
export interface BookingFormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  reason: string;
  isNewPatient: boolean;
  appointmentTypeId?: string;
  preferredDate?: Date;
  preferredTime?: string;
  notes?: string;
}

/**
 * Time slot availability
 * Represents a single available appointment slot
 */
export interface TimeSlot {
  start_time: string;
  end_time: string;
  is_available: boolean;
  dentist_id?: string;
  room_id?: string;
}

// ============================================
// Patient Forms
// ============================================

/**
 * Patient form data for create/edit operations
 * Includes personal, contact, and emergency information
 */
export interface PatientFormData {
  firstName: string;
  lastName: string;
  dateOfBirth: Date;
  gender: 'male' | 'female' | 'other';
  email: string;
  phone: string;
  street: string;
  city: string;
  state: string;
  zipCode: string;
  emergencyName: string;
  emergencyRelationship: string;
  emergencyPhone: string;
  medicalAlerts?: string[];
  insuranceProvider?: string;
  insurancePolicyNumber?: string;
  notes?: string;
}

// ============================================
// Appointment Forms
// ============================================

/**
 * Appointment form data for create/edit operations
 * Includes appointment details and scheduling information
 */
export interface AppointmentFormData {
  patient: string;
  patientName: string;
  time: string;
  duration: string;
  type: string;
  dentist: string;
  status: 'Pending' | 'Confirmed' | 'Completed' | 'Cancelled';
  notes?: string;
  treatmentPlanId?: string;
  roomId?: string;
}

/**
 * Appointment type definition
 * Describes available appointment types and their properties
 */
export interface AppointmentType {
  id: string;
  name: string;
  duration: number;
  description?: string;
  color?: string;
  icon?: string;
}

// ============================================
// Treatment Plan Forms
// ============================================

/**
 * Treatment plan form data for create/edit operations
 * Includes plan details and patient information
 */
export interface TreatmentPlanFormData {
  title: string;
  description?: string;
  patientId: string;
  patientName: string;
  notes?: string;
  procedures?: TreatmentProcedure[];
  estimatedCost?: number;
  estimatedDuration?: number;
}

/**
 * Individual treatment procedure
 * Part of a treatment plan
 */
export interface TreatmentProcedure {
  id: string;
  name: string;
  description?: string;
  estimatedCost: number;
  estimatedDuration: number;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed';
}

// ============================================
// Generic Form Utilities
// ============================================

/**
 * Generic form submission result
 * Used for standardized form handling
 */
export interface FormSubmissionResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  validationErrors?: Record<string, string[]>;
  timestamp: string;
}

/**
 * Form field error
 * Represents a single field validation error
 */
export interface FormFieldError {
  field: string;
  message: string;
  code?: string;
}

/**
 * Form state
 * Tracks form submission and validation state
 */
export interface FormState {
  isSubmitting: boolean;
  isValid: boolean;
  isDirty: boolean;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
}
