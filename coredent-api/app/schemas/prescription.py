"""
Prescription Schemas
Pydantic request/response models for prescription management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from enum import Enum


# ============================================
# ENUMS (mirrored for API)
# ============================================

class DrugScheduleEnum(str, Enum):
    SCHEDULE_I = "schedule_i"
    SCHEDULE_II = "schedule_ii"
    SCHEDULE_III = "schedule_iii"
    SCHEDULE_IV = "schedule_iv"
    SCHEDULE_V = "schedule_v"
    OTC = "otc"
    RX = "rx"


class PrescriptionStatusEnum(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISPENSED = "dispensed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class AllergySeverityEnum(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"


class AllergenTypeEnum(str, Enum):
    DRUG = "drug"
    DRUG_CLASS = "drug_class"
    FOOD = "food"
    ENVIRONMENTAL = "environmental"
    LATEX = "latex"
    OTHER = "other"


class InteractionSeverityEnum(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"


# ============================================
# MEDICATION SCHEMAS
# ============================================

class MedicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    generic_name: Optional[str] = None
    ndc_code: Optional[str] = None
    rxcui: Optional[str] = None
    drug_class: Optional[str] = None
    schedule: Optional[DrugScheduleEnum] = DrugScheduleEnum.RX
    is_controlled: bool = False
    form: Optional[str] = "tablet"
    strength: Optional[str] = None
    route: Optional[str] = "oral"
    common_dental_uses: Optional[str] = None
    default_dosage: Optional[str] = None
    default_frequency: Optional[str] = None
    default_duration_days: Optional[int] = None
    default_quantity: Optional[int] = None
    warnings: Optional[str] = None
    contraindications: Optional[str] = None
    pregnancy_category: Optional[str] = None


class MedicationCreate(MedicationBase):
    pass


class MedicationResponse(MedicationBase):
    id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MedicationSearchResult(BaseModel):
    """Result from OpenFDA drug search"""
    name: str
    generic_name: Optional[str] = None
    ndc_code: Optional[str] = None
    rxcui: Optional[str] = None
    drug_class: Optional[str] = None
    form: Optional[str] = None
    strength: Optional[str] = None
    route: Optional[str] = None
    manufacturer: Optional[str] = None
    source: str = "openfda"


# ============================================
# ALLERGY SCHEMAS
# ============================================

class PatientAllergyBase(BaseModel):
    allergen: str = Field(..., min_length=1, max_length=255)
    allergen_type: AllergenTypeEnum = AllergenTypeEnum.DRUG
    reaction: Optional[str] = None
    severity: AllergySeverityEnum = AllergySeverityEnum.MODERATE
    onset_date: Optional[date] = None
    reported_by: Optional[str] = None
    notes: Optional[str] = None


class PatientAllergyCreate(PatientAllergyBase):
    pass


class PatientAllergyUpdate(BaseModel):
    allergen: Optional[str] = None
    allergen_type: Optional[AllergenTypeEnum] = None
    reaction: Optional[str] = None
    severity: Optional[AllergySeverityEnum] = None
    onset_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    verified: Optional[bool] = None


class PatientAllergyResponse(PatientAllergyBase):
    id: UUID
    patient_id: UUID
    verified: bool = False
    verified_by: Optional[UUID] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# PATIENT MEDICATION SCHEMAS
# ============================================

class PatientMedicationBase(BaseModel):
    medication_name: str = Field(..., min_length=1, max_length=255)
    medication_id: Optional[UUID] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = "oral"
    prescriber: Optional[str] = None
    prescriber_phone: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class PatientMedicationCreate(PatientMedicationBase):
    pass


class PatientMedicationUpdate(BaseModel):
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    prescriber: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class PatientMedicationResponse(PatientMedicationBase):
    id: UUID
    patient_id: UUID
    is_active: bool = True
    entered_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# PRESCRIPTION SCHEMAS
# ============================================

class PrescriptionBase(BaseModel):
    medication_name: str = Field(..., min_length=1, max_length=255)
    medication_id: Optional[UUID] = None
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    form: Optional[str] = "tablet"
    route: Optional[str] = "oral"
    dosage: str = Field(..., min_length=1, max_length=255)
    frequency: str = Field(..., min_length=1, max_length=50)
    frequency_display: Optional[str] = None
    duration_days: Optional[int] = None
    quantity: int = Field(..., gt=0)
    quantity_unit: Optional[str] = "tablets"
    refills: int = Field(default=0, ge=0, le=12)
    sig: Optional[str] = None
    notes_to_pharmacist: Optional[str] = None
    internal_notes: Optional[str] = None
    dispense_as_written: bool = False
    substitution_allowed: bool = True
    pharmacy_name: Optional[str] = None
    pharmacy_phone: Optional[str] = None
    pharmacy_fax: Optional[str] = None
    pharmacy_address: Optional[str] = None
    diagnosis_codes: Optional[List[str]] = []


class PrescriptionCreate(PrescriptionBase):
    patient_id: UUID
    appointment_id: Optional[UUID] = None
    prescribed_date: Optional[date] = None  # Defaults to today

    @validator('refills')
    def validate_refills(cls, v, values):
        # Controlled substances typically limited to specific refill counts
        return min(v, 12)


class PrescriptionUpdate(BaseModel):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    frequency_display: Optional[str] = None
    duration_days: Optional[int] = None
    quantity: Optional[int] = None
    refills: Optional[int] = None
    sig: Optional[str] = None
    notes_to_pharmacist: Optional[str] = None
    internal_notes: Optional[str] = None
    pharmacy_name: Optional[str] = None
    pharmacy_phone: Optional[str] = None
    pharmacy_fax: Optional[str] = None
    pharmacy_address: Optional[str] = None
    status: Optional[PrescriptionStatusEnum] = None


class PrescriptionResponse(PrescriptionBase):
    id: UUID
    practice_id: UUID
    patient_id: UUID
    provider_id: UUID
    appointment_id: Optional[UUID] = None
    rx_number: str
    is_controlled: bool = False
    dea_schedule: Optional[DrugScheduleEnum] = None
    provider_dea_number: Optional[str] = None
    status: PrescriptionStatusEnum
    prescribed_date: date
    expiration_date: Optional[date] = None
    dispensed_date: Optional[date] = None
    cancelled_date: Optional[date] = None
    cancellation_reason: Optional[str] = None
    interaction_check_performed: bool = False
    interaction_check_results: Optional[List[dict]] = []
    allergy_check_performed: bool = False
    allergy_check_results: Optional[List[dict]] = []
    override_reason: Optional[str] = None
    refills_remaining: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PrescriptionCancel(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


# ============================================
# PRESCRIPTION TEMPLATE SCHEMAS
# ============================================

class PrescriptionTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = None
    description: Optional[str] = None
    medication_name: str = Field(..., min_length=1, max_length=255)
    medication_id: Optional[UUID] = None
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    form: Optional[str] = "tablet"
    route: Optional[str] = "oral"
    default_dosage: Optional[str] = None
    default_frequency: Optional[str] = None
    default_frequency_display: Optional[str] = None
    default_duration_days: Optional[int] = None
    default_quantity: Optional[int] = None
    default_quantity_unit: Optional[str] = "tablets"
    default_refills: int = 0
    default_sig: Optional[str] = None
    default_notes_to_pharmacist: Optional[str] = None
    dispense_as_written: bool = False


class PrescriptionTemplateCreate(PrescriptionTemplateBase):
    pass


class PrescriptionTemplateResponse(PrescriptionTemplateBase):
    id: UUID
    practice_id: UUID
    is_active: bool = True
    usage_count: int = 0
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# INTERACTION CHECK SCHEMAS
# ============================================

class InteractionCheckRequest(BaseModel):
    """Request to check drug interactions"""
    medication_name: str
    patient_id: UUID  # To check against patient's current medications


class InteractionResult(BaseModel):
    """Single interaction result"""
    drug_a: str
    drug_b: str
    severity: InteractionSeverityEnum
    description: str
    clinical_effects: Optional[str] = None
    management: Optional[str] = None
    source: Optional[str] = None


class InteractionCheckResponse(BaseModel):
    """Full interaction check response"""
    medication_checked: str
    patient_id: UUID
    has_interactions: bool = False
    has_allergy_conflicts: bool = False
    interactions: List[InteractionResult] = []
    allergy_warnings: List[dict] = []
    checked_at: datetime


# ============================================
# LIST RESPONSE WRAPPERS
# ============================================

class PrescriptionListResponse(BaseModel):
    prescriptions: List[PrescriptionResponse]
    count: int


class PatientAllergyListResponse(BaseModel):
    allergies: List[PatientAllergyResponse]
    count: int


class PatientMedicationListResponse(BaseModel):
    medications: List[PatientMedicationResponse]
    count: int


class PrescriptionTemplateListResponse(BaseModel):
    templates: List[PrescriptionTemplateResponse]
    count: int
