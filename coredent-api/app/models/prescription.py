"""
Prescription & Medication Models
Prescription writing, medication tracking, drug interactions, and allergy management
HIPAA: Full audit trail for controlled substance prescriptions (DEA compliance)
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Integer, Boolean, Date, Numeric, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.base import Base


# ============================================
# ENUMS
# ============================================

class DrugSchedule(str, enum.Enum):
    """DEA drug scheduling"""
    SCHEDULE_I = "schedule_i"       # No accepted medical use
    SCHEDULE_II = "schedule_ii"     # High abuse potential (opioids)
    SCHEDULE_III = "schedule_iii"   # Moderate abuse potential
    SCHEDULE_IV = "schedule_iv"     # Low abuse potential (benzodiazepines)
    SCHEDULE_V = "schedule_v"      # Lowest abuse potential
    OTC = "otc"                    # Over-the-counter
    RX = "rx"                      # Prescription only (non-scheduled)


class DrugForm(str, enum.Enum):
    """Drug dosage forms"""
    TABLET = "tablet"
    CAPSULE = "capsule"
    LIQUID = "liquid"
    INJECTION = "injection"
    TOPICAL = "topical"
    CREAM = "cream"
    OINTMENT = "ointment"
    GEL = "gel"
    SPRAY = "spray"
    DROPS = "drops"
    INHALER = "inhaler"
    PATCH = "patch"
    SUPPOSITORY = "suppository"
    RINSE = "rinse"
    POWDER = "powder"
    OTHER = "other"


class PrescriptionStatus(str, enum.Enum):
    """Prescription lifecycle status"""
    DRAFT = "draft"
    ACTIVE = "active"
    DISPENSED = "dispensed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class AllergySeverity(str, enum.Enum):
    """Allergy/reaction severity levels"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"


class AllergenType(str, enum.Enum):
    """Types of allergens"""
    DRUG = "drug"
    DRUG_CLASS = "drug_class"
    FOOD = "food"
    ENVIRONMENTAL = "environmental"
    LATEX = "latex"
    OTHER = "other"


class InteractionSeverity(str, enum.Enum):
    """Drug-drug interaction severity"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"


class FrequencyCode(str, enum.Enum):
    """Common prescription frequencies"""
    ONCE_DAILY = "qd"         # Once daily
    TWICE_DAILY = "bid"       # Twice daily
    THREE_DAILY = "tid"       # Three times daily
    FOUR_DAILY = "qid"        # Four times daily
    EVERY_4_HOURS = "q4h"     # Every 4 hours
    EVERY_6_HOURS = "q6h"     # Every 6 hours
    EVERY_8_HOURS = "q8h"     # Every 8 hours
    EVERY_12_HOURS = "q12h"   # Every 12 hours
    AS_NEEDED = "prn"         # As needed
    ONCE = "once"             # One-time dose
    WEEKLY = "weekly"         # Once a week
    CUSTOM = "custom"         # Custom schedule


# ============================================
# MODELS
# ============================================

class Medication(Base):
    """
    Drug/medication reference table.
    Stores drugs available for prescribing. Can be populated from
    OpenFDA or maintained manually by the practice.
    """
    __tablename__ = "medications"

    __table_args__ = (
        Index('idx_medication_name', 'name'),
        Index('idx_medication_generic', 'generic_name'),
        Index('idx_medication_ndc', 'ndc_code'),
        Index('idx_medication_active', 'is_active'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Drug identification
    name = Column(String(255), nullable=False)          # Brand name
    generic_name = Column(String(255))                  # Generic/INN name
    ndc_code = Column(String(20), unique=True)          # National Drug Code
    rxcui = Column(String(20))                          # RxNorm Concept Unique Identifier

    # Classification
    drug_class = Column(String(100))                    # e.g., "Antibiotic", "Analgesic"
    schedule = Column(Enum(DrugSchedule), default=DrugSchedule.RX)
    is_controlled = Column(Boolean, default=False)

    # Dosage form and strength
    form = Column(Enum(DrugForm), default=DrugForm.TABLET)
    strength = Column(String(100))                      # e.g., "500mg", "250mg/5mL"
    route = Column(String(50), default="oral")          # oral, topical, IV, IM, etc.

    # Dental-specific common uses
    common_dental_uses = Column(Text)                   # e.g., "Post-extraction pain"
    default_dosage = Column(String(100))
    default_frequency = Column(String(20))
    default_duration_days = Column(Integer)
    default_quantity = Column(Integer)

    # Warnings
    warnings = Column(Text)
    contraindications = Column(Text)
    pregnancy_category = Column(String(5))              # A, B, C, D, X

    # Status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    prescriptions = relationship("Prescription", back_populates="medication")
    templates = relationship("PrescriptionTemplate", back_populates="medication")

    def __repr__(self):
        return f"<Medication {self.name} ({self.strength})>"


class PatientAllergy(Base):
    """
    Patient allergy/adverse reaction records.
    Critical for drug interaction safety checking.
    """
    __tablename__ = "patient_allergies"

    __table_args__ = (
        Index('idx_patient_allergy_patient', 'patient_id'),
        Index('idx_patient_allergy_active', 'patient_id', 'is_active'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)

    # Allergen details
    allergen = Column(String(255), nullable=False)      # Drug name, class, or substance
    allergen_type = Column(Enum(AllergenType), default=AllergenType.DRUG)

    # Reaction details
    reaction = Column(Text)                             # Description of reaction
    severity = Column(Enum(AllergySeverity), default=AllergySeverity.MODERATE)
    onset_date = Column(Date)                           # When allergy was first noted

    # Source
    reported_by = Column(String(100))                   # "Patient", "Provider", "Transfer"
    verified = Column(Boolean, default=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="allergies")
    verified_user = relationship("User", foreign_keys=[verified_by])

    def __repr__(self):
        return f"<PatientAllergy {self.allergen} ({self.severity})>"


class PatientMedication(Base):
    """
    Patient's current/active medication list.
    Tracks medications prescribed elsewhere (not just from this practice).
    Used for comprehensive drug interaction checking.
    """
    __tablename__ = "patient_medications"

    __table_args__ = (
        Index('idx_patient_medication_patient', 'patient_id'),
        Index('idx_patient_medication_active', 'patient_id', 'is_active'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)

    # Medication info (may or may not link to our Medication table)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"))
    medication_name = Column(String(255), nullable=False)  # Free-text for external meds
    dosage = Column(String(100))
    frequency = Column(String(50))
    route = Column(String(50), default="oral")

    # Prescriber info
    prescriber = Column(String(255))                    # External prescriber name
    prescriber_phone = Column(String(20))

    # Dates
    start_date = Column(Date)
    end_date = Column(Date)

    # Status
    is_active = Column(Boolean, default=True)
    reason = Column(Text)                               # Reason for medication
    notes = Column(Text)

    # Who entered it
    entered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="current_medications")
    medication = relationship("Medication")
    entered_user = relationship("User", foreign_keys=[entered_by])

    def __repr__(self):
        return f"<PatientMedication {self.medication_name} for Patient {self.patient_id}>"


class Prescription(Base):
    """
    Prescription records written by providers.
    HIPAA: Full audit trail required for controlled substances.
    DEA: Controlled substance prescriptions require valid DEA number.
    """
    __tablename__ = "prescriptions"

    __table_args__ = (
        Index('idx_prescription_patient', 'patient_id'),
        Index('idx_prescription_provider', 'provider_id'),
        Index('idx_prescription_status', 'status'),
        Index('idx_prescription_date', 'prescribed_date'),
        Index('idx_prescription_practice', 'practice_id'),
        Index('idx_prescription_controlled', 'is_controlled'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"))
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"))

    # Prescription number (auto-generated, practice-unique)
    rx_number = Column(String(50), unique=True, nullable=False)

    # Medication details (denormalized for the Rx record)
    medication_name = Column(String(255), nullable=False)
    generic_name = Column(String(255))
    strength = Column(String(100))
    form = Column(String(50))
    route = Column(String(50), default="oral")

    # Dosage instructions
    dosage = Column(String(255), nullable=False)        # e.g., "1 tablet"
    frequency = Column(String(50), nullable=False)      # e.g., "bid", "q6h"
    frequency_display = Column(String(255))             # Human-readable: "Twice daily"
    duration_days = Column(Integer)                      # Duration in days
    quantity = Column(Integer, nullable=False)           # Total quantity to dispense
    quantity_unit = Column(String(50), default="tablets") # tablets, capsules, mL, etc.
    refills = Column(Integer, default=0)                 # Number of refills authorized
    refills_remaining = Column(Integer, default=0)

    # Special instructions
    sig = Column(Text)                                   # Full sig (directions)
    notes_to_pharmacist = Column(Text)
    internal_notes = Column(Text)                        # Provider-only notes

    # DAW (Dispense As Written)
    dispense_as_written = Column(Boolean, default=False)
    substitution_allowed = Column(Boolean, default=True)

    # Controlled substance tracking
    is_controlled = Column(Boolean, default=False)
    dea_schedule = Column(Enum(DrugSchedule))
    provider_dea_number = Column(String(20))             # Provider's DEA number for this Rx

    # Pharmacy info
    pharmacy_name = Column(String(255))
    pharmacy_phone = Column(String(20))
    pharmacy_fax = Column(String(20))
    pharmacy_address = Column(Text)
    pharmacy_npi = Column(String(20))

    # Status and dates
    status = Column(Enum(PrescriptionStatus), default=PrescriptionStatus.DRAFT)
    prescribed_date = Column(Date, nullable=False)
    expiration_date = Column(Date)                       # Typically 1 year, 90 days for controlled
    dispensed_date = Column(Date)
    cancelled_date = Column(Date)
    cancellation_reason = Column(Text)

    # Interaction check results (stored for audit)
    interaction_check_performed = Column(Boolean, default=False)
    interaction_check_results = Column(JSON, default=list)  # Array of flagged interactions
    allergy_check_performed = Column(Boolean, default=False)
    allergy_check_results = Column(JSON, default=list)      # Array of flagged allergies
    override_reason = Column(Text)                           # If provider overrides warnings

    # Diagnosis / ICD codes
    diagnosis_codes = Column(JSON, default=list)         # Array of ICD-10 codes

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    practice = relationship("Practice")
    patient = relationship("Patient", back_populates="prescriptions")
    provider = relationship("User", back_populates="prescriptions")
    medication = relationship("Medication", back_populates="prescriptions")
    appointment = relationship("Appointment")

    def __repr__(self):
        return f"<Prescription {self.rx_number} - {self.medication_name} ({self.status})>"


class PrescriptionTemplate(Base):
    """
    Quick-prescribe templates for commonly prescribed medications.
    Practice-specific, pre-fills the prescription form.
    """
    __tablename__ = "prescription_templates"

    __table_args__ = (
        Index('idx_rx_template_practice', 'practice_id'),
        Index('idx_rx_template_active', 'is_active'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"))

    # Template info
    name = Column(String(255), nullable=False)          # e.g., "Post-Extraction Amoxicillin"
    category = Column(String(100))                      # e.g., "Antibiotics", "Pain Management"
    description = Column(Text)

    # Pre-filled values
    medication_name = Column(String(255), nullable=False)
    generic_name = Column(String(255))
    strength = Column(String(100))
    form = Column(String(50))
    route = Column(String(50), default="oral")
    default_dosage = Column(String(255))
    default_frequency = Column(String(50))
    default_frequency_display = Column(String(255))
    default_duration_days = Column(Integer)
    default_quantity = Column(Integer)
    default_quantity_unit = Column(String(50), default="tablets")
    default_refills = Column(Integer, default=0)
    default_sig = Column(Text)
    default_notes_to_pharmacist = Column(Text)
    dispense_as_written = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)             # Track template popularity

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    practice = relationship("Practice")
    medication = relationship("Medication", back_populates="templates")
    creator = relationship("User")

    def __repr__(self):
        return f"<PrescriptionTemplate {self.name}>"


class DrugInteraction(Base):
    """
    Known drug-drug interaction pairs.
    Populated from FDA/medical databases and augmented by practice.
    """
    __tablename__ = "drug_interactions"

    __table_args__ = (
        Index('idx_drug_interaction_a', 'drug_a_name'),
        Index('idx_drug_interaction_b', 'drug_b_name'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Can reference medication records or be free-text for external drugs
    drug_a_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"))
    drug_b_id = Column(UUID(as_uuid=True), ForeignKey("medications.id"))
    drug_a_name = Column(String(255), nullable=False)
    drug_b_name = Column(String(255), nullable=False)

    # Interaction details
    severity = Column(Enum(InteractionSeverity), nullable=False)
    description = Column(Text, nullable=False)
    clinical_effects = Column(Text)
    management = Column(Text)                           # How to manage the interaction
    source = Column(String(100))                        # "FDA", "DrugBank", "Manual"

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    drug_a = relationship("Medication", foreign_keys=[drug_a_id])
    drug_b = relationship("Medication", foreign_keys=[drug_b_id])

    def __repr__(self):
        return f"<DrugInteraction {self.drug_a_name} ↔ {self.drug_b_name} ({self.severity})>"
