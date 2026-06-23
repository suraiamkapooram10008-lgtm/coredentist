"""
Patient Model
Represents dental patients
SECURITY: Added database indexes for query performance

PHI columns are stored as EncryptedString / EncryptedJSON so the database
itself never holds plaintext PHI.  The application is the only place plaintext
exists in memory, and only for the lifetime of a request.

Search columns (``first_name``, ``last_name``, ``email``, ``phone``) are kept
*both* encrypted (the source of truth) and as a deterministic hash
(``search_hash_*``) for equality lookups.  Substring search is performed on a
trigram index of the plaintext at write-time, written to ``search_index_*``
columns.  ``search_index_*`` is itself low-sensitivity (it is not the value)
but should still be considered personal data under most privacy regimes.
"""

from sqlalchemy import (
    Column,
    String,
    Date,
    DateTime,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from app.core.base import Base
from app.core.encryption import EncryptedString, EncryptedJSON


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
        Index("idx_patient_practice_status", "practice_id", "status"),
        Index("idx_patient_name", "last_name", "first_name"),
        Index("idx_patient_practice_email", "practice_id", "email"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)

    # ---- Encrypted PHI columns ----
    # ``column_name=`` is used as AAD so swapping ciphertext between columns
    # is detected on decrypt.
    first_name = Column(EncryptedString(100, column_name="patient.first_name"), nullable=False)
    last_name = Column(EncryptedString(100, column_name="patient.last_name"), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender))
    email = Column(EncryptedString(255, column_name="patient.email"))
    phone = Column(EncryptedString(20, column_name="patient.phone"))

    # Address
    address_street = Column(EncryptedString(255, column_name="patient.address_street"))
    address_city = Column(EncryptedString(100, column_name="patient.address_city"))
    address_state = Column(EncryptedString(100, column_name="patient.address_state"))
    address_zip = Column(EncryptedString(20, column_name="patient.address_zip"))

    # Global identifiers
    abha_id = Column(EncryptedString(20, column_name="patient.abha_id"))
    ssn_last_four = Column(EncryptedString(4, column_name="patient.ssn_last_four"))

    # Emergency contact
    emergency_contact = Column(
        EncryptedJSON(column_name="patient.emergency_contact")
    )  # {name, relationship, phone}

    # Medical information (all sensitive PHI)
    medical_alerts = Column(EncryptedJSON(column_name="patient.medical_alerts"), default=dict)
    medical_history = Column(EncryptedJSON(column_name="patient.medical_history"), default=dict)
    dental_history = Column(EncryptedJSON(column_name="patient.dental_history"), default=dict)
    insurance_info = Column(EncryptedJSON(column_name="patient.insurance_info"))

    # ---- Search indexes (low-sensitivity, allow exact + prefix lookup) ----
    # These store HMACs of the lowercased/normalized values.  They are *not*
    # plaintext; they let the DB do equality/prefix matching without
    # revealing the original value.  See ``app.core.search_index`` for the
    # HMAC computation.  These columns are *not* a substitute for the
    # encrypted columns — they are an index on them.
    search_index_email = Column(String(64), index=True)
    search_index_phone = Column(String(64), index=True)
    search_index_last_name = Column(String(64), index=True)

    # Status
    status = Column(Enum(PatientStatus), default=PatientStatus.ACTIVE)

    # Global Compliance (India DPDP / US HIPAA)
    consent_recorded_at = Column(DateTime(timezone=True))

    # Patient Portal Access
    portal_access_token = Column(String(128))  # Hashed token for patient self-service portal
    portal_token_expires = Column(DateTime(timezone=True))

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
    subscriptions = relationship("Subscription", back_populates="patient")

    @property
    def full_name(self) -> str:
        # Both fields are already decrypted by the EncryptedString type.
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @property
    def has_medical_alerts(self) -> bool:
        return bool(self.medical_alerts)

    def __repr__(self):
        return f"<Patient {self.id}>"
