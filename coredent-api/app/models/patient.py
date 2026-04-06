"""
Patient Model
Represents dental patients
SECURITY: Added database indexes for query performance
"""

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Enum, ARRAY, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.base import Base


class PatientStatus(str, enum.Enum):
    """Patient status"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class Gender(str, enum.Enum):
    """Gender options"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Patient(Base):
    """Patient model"""
    __tablename__ = "patients"
    
    # PERFORMANCE: Add composite indexes for common query patterns
    __table_args__ = (
        Index('idx_patient_practice_status', 'practice_id', 'status'),
        Index('idx_patient_name', 'last_name', 'first_name'),
        Index('idx_patient_practice_email', 'practice_id', 'email'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender))
    email = Column(String(255), index=True)  # Already has index
    phone = Column(String(20), index=True)  # Added index for phone lookups
    
    # Address (Expanded for Global/India Portability)
    address_street = Column(String(255))
    address_city = Column(String(100))
    address_state = Column(String(100)) # Expanded from 2 chars for Indian states
    address_zip = Column(String(20))
    
    # Global Identifiers
    abha_id = Column(String(20), index=True) # India's ABHA ID
    ssn_last_four = Column(String(4)) # US PHI (Standardized)
    
    # Emergency Contact
    emergency_contact = Column(JSON)  # {name, relationship, phone}
    
    # Medical Information
    # Use JSON for lists/dicts for SQLite compatibility (ARRAY is Postgres-only).
    # Stored as JSON arrays.
    medical_alerts = Column(JSON, default=[])
    medical_history = Column(JSON, default={})
    dental_history = Column(JSON, default={})
    insurance_info = Column(JSON)
    
    # Status
    status = Column(Enum(PatientStatus), default=PatientStatus.ACTIVE)
    
    # Global Compliance (India DPDP / US HIPAA)
    consent_recorded_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="patients")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    clinical_notes = relationship("ClinicalNote", back_populates="patient", cascade="all, delete-orphan")
    dental_chart = relationship("DentalChart", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    perio_charts = relationship("PerioChart", back_populates="patient", cascade="all, delete-orphan")
    treatment_plans = relationship("TreatmentPlan", back_populates="patient", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="patient", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="patient", cascade="all, delete-orphan")
    insurances = relationship("PatientInsurance", back_populates="patient", cascade="all, delete-orphan")
    insurance_claims = relationship("InsuranceClaim", back_populates="patient", cascade="all, delete-orphan")
    pre_authorizations = relationship("InsurancePreAuthorization", back_populates="patient", cascade="all, delete-orphan")
    eligibility = relationship("Eligibility", back_populates="patient", cascade="all, delete-orphan")
    images = relationship("PatientImage", back_populates="patient", cascade="all, delete-orphan")
    online_bookings = relationship("OnlineBooking", back_populates="patient", cascade="all, delete-orphan")
    waitlist_entries = relationship("WaitlistEntry", back_populates="patient", cascade="all, delete-orphan")
    lab_cases = relationship("LabCase", back_populates="patient", cascade="all, delete-orphan")
    referrals = relationship("Referral", back_populates="patient", cascade="all, delete-orphan")
    messages = relationship("PatientMessage", back_populates="patient", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="patient", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="patient", cascade="all, delete-orphan")
    payment_cards = relationship("PaymentCard", back_populates="patient")
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def has_medical_alerts(self) -> bool:
        return len(self.medical_alerts) > 0 if self.medical_alerts else False
    
    def __repr__(self):
        return f"<Patient {self.full_name}>"
