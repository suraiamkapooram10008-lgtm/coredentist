/**
 * Prescription API Service
 * Handles all prescription management, drug search, allergy, and medication list operations
 */

import { apiClient } from './api';

// ============================================
// TYPES
// ============================================

export interface Medication {
  id: string;
  name: string;
  generic_name?: string;
  ndc_code?: string;
  rxcui?: string;
  drug_class?: string;
  schedule?: string;
  is_controlled?: boolean;
  form?: string;
  strength?: string;
  route?: string;
  common_dental_uses?: string;
  default_dosage?: string;
  default_frequency?: string;
  default_duration_days?: number;
  default_quantity?: number;
  warnings?: string;
  contraindications?: string;
  pregnancy_category?: string;
  is_active?: boolean;
}

export interface PatientAllergy {
  id: string;
  patient_id: string;
  allergen: string;
  allergen_type: 'drug' | 'drug_class' | 'food' | 'environmental' | 'latex' | 'other';
  reaction?: string;
  severity: 'mild' | 'moderate' | 'severe' | 'life_threatening';
  onset_date?: string;
  reported_by?: string;
  verified?: boolean;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PatientMedication {
  id: string;
  patient_id: string;
  medication_id?: string;
  medication_name: string;
  dosage?: string;
  frequency?: string;
  route?: string;
  prescriber?: string;
  prescriber_phone?: string;
  start_date?: string;
  end_date?: string;
  is_active: boolean;
  reason?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Prescription {
  id: string;
  practice_id: string;
  patient_id: string;
  provider_id: string;
  medication_id?: string;
  appointment_id?: string;
  rx_number: string;
  medication_name: string;
  generic_name?: string;
  strength?: string;
  form?: string;
  route?: string;
  dosage: string;
  frequency: string;
  frequency_display?: string;
  duration_days?: number;
  quantity: number;
  quantity_unit?: string;
  refills: number;
  refills_remaining?: number;
  sig?: string;
  notes_to_pharmacist?: string;
  internal_notes?: string;
  dispense_as_written?: boolean;
  substitution_allowed?: boolean;
  is_controlled: boolean;
  dea_schedule?: string;
  pharmacy_name?: string;
  pharmacy_phone?: string;
  status: 'draft' | 'active' | 'dispensed' | 'completed' | 'cancelled' | 'expired';
  prescribed_date: string;
  expiration_date?: string;
  dispensed_date?: string;
  cancelled_date?: string;
  cancellation_reason?: string;
  interaction_check_performed?: boolean;
  interaction_check_results?: InteractionResult[];
  allergy_check_performed?: boolean;
  allergy_check_results?: AllergyWarning[];
  override_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface InteractionResult {
  drug_a: string;
  drug_b: string;
  severity: 'minor' | 'moderate' | 'major' | 'contraindicated';
  description: string;
  clinical_effects?: string;
  management?: string;
  source?: string;
}

export interface AllergyWarning {
  allergen: string;
  allergen_type: string;
  reaction?: string;
  severity: string;
  message: string;
}

export interface PrescriptionTemplate {
  id: string;
  practice_id: string;
  name: string;
  category?: string;
  description?: string;
  medication_name: string;
  generic_name?: string;
  strength?: string;
  form?: string;
  route?: string;
  default_dosage?: string;
  default_frequency?: string;
  default_frequency_display?: string;
  default_duration_days?: number;
  default_quantity?: number;
  default_quantity_unit?: string;
  default_refills?: number;
  default_sig?: string;
  default_notes_to_pharmacist?: string;
  dispense_as_written?: boolean;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface InteractionCheckResponse {
  medication_checked: string;
  patient_id: string;
  has_interactions: boolean;
  has_allergy_conflicts: boolean;
  interactions: InteractionResult[];
  allergy_warnings: AllergyWarning[];
  checked_at: string;
}

// ============================================
// CREATE/UPDATE TYPES
// ============================================

export interface PrescriptionCreateData {
  patient_id: string;
  medication_name: string;
  medication_id?: string;
  generic_name?: string;
  strength?: string;
  form?: string;
  route?: string;
  dosage: string;
  frequency: string;
  frequency_display?: string;
  duration_days?: number;
  quantity: number;
  quantity_unit?: string;
  refills?: number;
  sig?: string;
  notes_to_pharmacist?: string;
  internal_notes?: string;
  dispense_as_written?: boolean;
  substitution_allowed?: boolean;
  pharmacy_name?: string;
  pharmacy_phone?: string;
  pharmacy_fax?: string;
  pharmacy_address?: string;
  prescribed_date?: string;
  appointment_id?: string;
  diagnosis_codes?: string[];
}

export interface AllergyCreateData {
  allergen: string;
  allergen_type?: string;
  reaction?: string;
  severity?: string;
  onset_date?: string;
  reported_by?: string;
  notes?: string;
}

export interface MedicationCreateData {
  medication_name: string;
  medication_id?: string;
  dosage?: string;
  frequency?: string;
  route?: string;
  prescriber?: string;
  prescriber_phone?: string;
  start_date?: string;
  end_date?: string;
  reason?: string;
  notes?: string;
}

export interface TemplateCreateData {
  name: string;
  category?: string;
  description?: string;
  medication_name: string;
  medication_id?: string;
  generic_name?: string;
  strength?: string;
  form?: string;
  route?: string;
  default_dosage?: string;
  default_frequency?: string;
  default_frequency_display?: string;
  default_duration_days?: number;
  default_quantity?: number;
  default_quantity_unit?: string;
  default_refills?: number;
  default_sig?: string;
  default_notes_to_pharmacist?: string;
  dispense_as_written?: boolean;
}

// ============================================
// API FUNCTIONS
// ============================================

const BASE = '/prescriptions';

// --- Prescriptions ---

export const prescriptionApi = {
  // List prescriptions with filters
  list: async (params?: {
    patient_id?: string;
    status?: string;
    provider_id?: string;
    is_controlled?: boolean;
    start_date?: string;
    end_date?: string;
    page?: number;
    limit?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.set(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    const { data } = await apiClient.get(`${BASE}/${query ? `?${query}` : ''}`);
    return data;
  },

  // Get single prescription
  get: async (id: string) => {
    const { data } = await apiClient.get(`${BASE}/${id}`);
    return data;
  },

  // Create prescription
  create: async (rxData: PrescriptionCreateData) => {
    const { data } = await apiClient.post(`${BASE}/`, rxData);
    return data;
  },

  // Update prescription
  update: async (id: string, rxData: Partial<PrescriptionCreateData>) => {
    const { data } = await apiClient.put(`${BASE}/${id}`, rxData);
    return data;
  },

  // Cancel prescription
  cancel: async (id: string, reason: string) => {
    const { data } = await apiClient.post(`${BASE}/${id}/cancel`, { reason });
    return data;
  },

  // Get patient prescriptions
  getByPatient: async (patientId: string, status?: string) => {
    const params = status ? `?status=${status}` : '';
    const { data } = await apiClient.get(`${BASE}/patient/${patientId}${params}`);
    return data;
  },

  // --- Medication Search ---
  searchMedications: async (query: string, source: 'local' | 'openfda' | 'all' = 'all') => {
    const { data } = await apiClient.get(`${BASE}/medications/search?q=${encodeURIComponent(query)}&source=${source}`);
    return data;
  },

  // Check drug interactions
  checkInteractions: async (medicationName: string, patientId: string): Promise<InteractionCheckResponse> => {
    const { data } = await apiClient.post(`${BASE}/medications/check-interactions`, {
      medication_name: medicationName,
      patient_id: patientId,
    });
    return data;
  },

  // Seed common medications
  seedMedications: async () => {
    const { data } = await apiClient.post(`${BASE}/medications/seed`);
    return data;
  },

  // --- Patient Allergies ---
  getAllergies: async (patientId: string, includeInactive = false) => {
    const { data } = await apiClient.get(
      `${BASE}/patients/${patientId}/allergies?include_inactive=${includeInactive}`
    );
    return data;
  },

  addAllergy: async (patientId: string, allergyData: AllergyCreateData) => {
    const { data } = await apiClient.post(`${BASE}/patients/${patientId}/allergies`, allergyData);
    return data;
  },

  updateAllergy: async (patientId: string, allergyId: string, allergyData: Partial<AllergyCreateData>) => {
    const { data } = await apiClient.put(
      `${BASE}/patients/${patientId}/allergies/${allergyId}`,
      allergyData
    );
    return data;
  },

  deleteAllergy: async (patientId: string, allergyId: string) => {
    const { data } = await apiClient.delete(`${BASE}/patients/${patientId}/allergies/${allergyId}`);
    return data;
  },

  // --- Patient Current Medications ---
  getMedications: async (patientId: string, activeOnly = true) => {
    const { data } = await apiClient.get(
      `${BASE}/patients/${patientId}/medications?active_only=${activeOnly}`
    );
    return data;
  },

  addMedication: async (patientId: string, medData: MedicationCreateData) => {
    const { data } = await apiClient.post(`${BASE}/patients/${patientId}/medications`, medData);
    return data;
  },

  updateMedication: async (patientId: string, medId: string, medData: Partial<MedicationCreateData>) => {
    const { data } = await apiClient.put(
      `${BASE}/patients/${patientId}/medications/${medId}`,
      medData
    );
    return data;
  },

  // --- Prescription Templates ---
  getTemplates: async (category?: string, search?: string) => {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    if (search) params.set('search', search);
    const query = params.toString();
    const { data } = await apiClient.get(`${BASE}/templates/${query ? `?${query}` : ''}`);
    return data;
  },

  createTemplate: async (templateData: TemplateCreateData) => {
    const { data } = await apiClient.post(`${BASE}/templates/`, templateData);
    return data;
  },

  deleteTemplate: async (templateId: string) => {
    const { data } = await apiClient.delete(`${BASE}/templates/${templateId}`);
    return data;
  },
};

// ============================================
// FREQUENCY HELPERS
// ============================================

export const FREQUENCY_OPTIONS = [
  { value: 'qd', label: 'Once daily' },
  { value: 'bid', label: 'Twice daily' },
  { value: 'tid', label: 'Three times daily' },
  { value: 'qid', label: 'Four times daily' },
  { value: 'q4h', label: 'Every 4 hours' },
  { value: 'q6h', label: 'Every 6 hours' },
  { value: 'q8h', label: 'Every 8 hours' },
  { value: 'q12h', label: 'Every 12 hours' },
  { value: 'prn', label: 'As needed' },
  { value: 'once', label: 'One time only' },
  { value: 'weekly', label: 'Once weekly' },
];

export const DRUG_FORMS = [
  'tablet', 'capsule', 'liquid', 'injection', 'topical',
  'cream', 'ointment', 'gel', 'spray', 'drops',
  'inhaler', 'patch', 'suppository', 'rinse', 'powder',
];

export const SEVERITY_COLORS = {
  mild: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  moderate: 'text-orange-600 bg-orange-50 border-orange-200',
  severe: 'text-red-600 bg-red-50 border-red-200',
  life_threatening: 'text-red-800 bg-red-100 border-red-300',
  minor: 'text-blue-600 bg-blue-50 border-blue-200',
  major: 'text-red-600 bg-red-50 border-red-200',
  contraindicated: 'text-red-900 bg-red-200 border-red-400',
};

export const STATUS_COLORS: Record<string, string> = {
  draft: 'text-gray-600 bg-gray-100',
  active: 'text-green-700 bg-green-100',
  dispensed: 'text-blue-700 bg-blue-100',
  completed: 'text-emerald-700 bg-emerald-100',
  cancelled: 'text-red-700 bg-red-100',
  expired: 'text-amber-700 bg-amber-100',
};
