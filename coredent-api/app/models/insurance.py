"""
Insurance Models
Insurance carriers, patient insurance, claims, and payments
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Numeric, Date, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class InsuranceType(str, enum.Enum):
    """Insurance type"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class ClaimStatus(str, enum.Enum):
    """Claim status"""
    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    DENIED = "denied"
    PAID = "paid"
    APPEALED = "appealed"


class RelationshipToSubscriber(str, enum.Enum):
    """Patient relationship to insurance subscriber"""
    SELF = "self"
    SPOUSE = "spouse"
    CHILD = "child"
    OTHER = "other"


class InsuranceCarrier(Base):
    """Insurance carrier/company model"""
    __tablename__ = "insurance_carriers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(20))
    fax = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))
    
    # EDI Information
    payer_id = Column(String(50), unique=True, index=True)  # Electronic payer ID
    edi_enabled = Column(Boolean, default=False)
    
    # Notes
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    patient_insurances = relationship("PatientInsurance", back_populates="carrier")
    claims = relationship("InsuranceClaim", back_populates="carrier")
    eligibility = relationship("Eligibility", back_populates="carrier")
    
    def __repr__(self):
        return f"<InsuranceCarrier {self.name}>"


class PatientInsurance(Base):
    """Patient insurance information"""
    __tablename__ = "patient_insurances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    carrier_id = Column(UUID(as_uuid=True), ForeignKey("insurance_carriers.id"), nullable=False)
    
    insurance_type = Column(Enum(InsuranceType), default=InsuranceType.PRIMARY)
    
    # Subscriber Information
    subscriber_id = Column(String(50), nullable=False)  # Member/Policy ID
    group_number = Column(String(50))
    relationship_to_subscriber = Column(Enum(RelationshipToSubscriber), default=RelationshipToSubscriber.SELF)
    
    # Subscriber Details (if not self)
    subscriber_first_name = Column(String(100))
    subscriber_last_name = Column(String(100))
    subscriber_dob = Column(Date)
    subscriber_ssn = Column(String(11))  # Encrypted in production
    
    # Coverage Details
    effective_date = Column(Date)
    termination_date = Column(Date)
    
    # Benefits
    annual_maximum = Column(Numeric(10, 2))
    annual_deductible = Column(Numeric(10, 2))
    deductible_met = Column(Numeric(10, 2), default=0)
    
    # Coverage Percentages
    preventive_coverage = Column(Integer, default=100)  # Percentage
    basic_coverage = Column(Integer, default=80)
    major_coverage = Column(Integer, default=50)
    
    # Employer Information
    employer_name = Column(String(255))
    
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="insurances")
    carrier = relationship("InsuranceCarrier", back_populates="patient_insurances")
    claims = relationship("InsuranceClaim", back_populates="patient_insurance")
    
    def __repr__(self):
        return f"<PatientInsurance {self.patient_id} - {self.insurance_type}>"


class InsuranceClaim(Base):
    """Insurance claim model"""
    __tablename__ = "insurance_claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    patient_insurance_id = Column(UUID(as_uuid=True), ForeignKey("patient_insurances.id"), nullable=False)
    carrier_id = Column(UUID(as_uuid=True), ForeignKey("insurance_carriers.id"), nullable=False)
    
    # Claim Information
    claim_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(Enum(ClaimStatus), default=ClaimStatus.DRAFT)
    
    # Dates
    service_date = Column(Date, nullable=False)
    submission_date = Column(Date)
    received_date = Column(Date)
    paid_date = Column(Date)
    
    # Financial
    billed_amount = Column(Numeric(10, 2), nullable=False)
    allowed_amount = Column(Numeric(10, 2))
    deductible_amount = Column(Numeric(10, 2), default=0)
    copay_amount = Column(Numeric(10, 2), default=0)
    paid_amount = Column(Numeric(10, 2), default=0)
    patient_responsibility = Column(Numeric(10, 2), default=0)
    
    # Procedure Codes (stored as JSON array)
    # Structure: [{ code: "D0120", description: "Periodic oral evaluation", fee: 75.00 }]
    procedure_codes = Column(Text)  # JSON string
    
    # Diagnosis Codes
    diagnosis_codes = Column(Text)  # JSON string
    
    # Notes and Attachments
    notes = Column(Text)
    denial_reason = Column(Text)
    
    # EDI Information
    edi_transaction_id = Column(String(100))
    edi_batch_id = Column(String(100))
    confirmation_number = Column(String(100))  # From clearinghouse
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="insurance_claims")
    patient = relationship("Patient", back_populates="insurance_claims")
    patient_insurance = relationship("PatientInsurance", back_populates="claims")
    carrier = relationship("InsuranceCarrier", back_populates="claims")
    
    @property
    def outstanding_balance(self) -> float:
        """Calculate outstanding balance"""
        return float(self.billed_amount or 0) - float(self.paid_amount or 0)
    
    def __repr__(self):
        return f"<InsuranceClaim {self.claim_number} - {self.status}>"


class InsurancePreAuthorization(Base):
    """Insurance pre-authorization model"""
    __tablename__ = "insurance_pre_authorizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    patient_insurance_id = Column(UUID(as_uuid=True), ForeignKey("patient_insurances.id"), nullable=False)
    
    # Authorization Information
    authorization_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(50), default="pending")  # pending, approved, denied
    
    # Dates
    request_date = Column(Date, nullable=False)
    approval_date = Column(Date)
    expiration_date = Column(Date)
    
    # Treatment Information
    procedure_codes = Column(Text)  # JSON string
    estimated_cost = Column(Numeric(10, 2))
    approved_amount = Column(Numeric(10, 2))
    
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="pre_authorizations")
    patient_insurance = relationship("PatientInsurance")
    
    def __repr__(self):
        return f"<PreAuthorization {self.authorization_number} - {self.status}>"
        
        # Eligibility model
        class Eligibility(Base):
            """Eligibility verification result"""
            __tablename__ = "eligibility"
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
            patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
            patient_insurance_id = Column(UUID(as_uuid=True), ForeignKey("patient_insurances.id"), nullable=False)
            carrier_id = Column(UUID(as_uuid=True), ForeignKey("insurance_carriers.id"), nullable=False)
            verified_at = Column(DateTime(timezone=True), server_default=func.now())
            is_active = Column(Boolean, default=True)
            # Coverage details
            coverage_status = Column(String(50))
            remaining_benefits = Column(Numeric(10, 2))
            deductible_remaining = Column(Numeric(10, 2))
            notes = Column(Text)
            # Relationships
            patient = relationship("Patient", back_populates="eligibility")
            patient_insurance = relationship("PatientInsurance", back_populates="eligibility")
            carrier = relationship("InsuranceCarrier", back_populates="eligibility")
            def __repr__(self):
                return f"<Eligibility {self.id} - {self.coverage_status}>"
        
        # Explanation of Benefits model
        class ExplanationOfBenefits(Base):
            """EOB for a claim"""
            __tablename__ = "explanations_of_benefits"
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
            claim_id = Column(UUID(as_uuid=True), ForeignKey("insurance_claims.id"), nullable=False)
            generated_at = Column(DateTime(timezone=True), server_default=func.now())
            description = Column(Text)
            amount_covered = Column(Numeric(10, 2))
            amount_patient_responsibility = Column(Numeric(10, 2))
            # Relationships
            claim = relationship("InsuranceClaim", back_populates="eob")
            def __repr__(self):
                return f"<EOB {self.id} for Claim {self.claim_id}>"
        
        # New models for Eligibility and Explanation of Benefits (EOB)
        class Eligibility(Base):
            """Eligibility verification result"""
            __tablename__ = "eligibility"
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
            patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
            patient_insurance_id = Column(UUID(as_uuid=True), ForeignKey("patient_insurances.id"), nullable=False)
            carrier_id = Column(UUID(as_uuid=True), ForeignKey("insurance_carriers.id"), nullable=False)
            verified_at = Column(DateTime(timezone=True), server_default=func.now())
            is_active = Column(Boolean, default=True)
            # Coverage details
            coverage_status = Column(String(50))  # e.g., "covered", "not_covered"
            remaining_benefits = Column(Numeric(10, 2))
            deductible_remaining = Column(Numeric(10, 2))
            notes = Column(Text)
            # Relationships
            patient = relationship("Patient", back_populates="eligibility")
            patient_insurance = relationship("PatientInsurance", back_populates="eligibility")
            carrier = relationship("InsuranceCarrier", back_populates="eligibility")
            def __repr__(self):
                return f"<Eligibility {self.id} - {self.coverage_status}>"
        
        class ExplanationOfBenefits(Base):
            """EOB for a claim"""
            __tablename__ = "explanations_of_benefits"
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
            claim_id = Column(UUID(as_uuid=True), ForeignKey("insurance_claims.id"), nullable=False)
            generated_at = Column(DateTime(timezone=True), server_default=func.now())
            description = Column(Text)
            amount_covered = Column(Numeric(10, 2))
            amount_patient_responsibility = Column(Numeric(10, 2))
            # Relationships
            claim = relationship("InsuranceClaim", back_populates="eob")
            def __repr__(self):
                return f"<EOB {self.id} for Claim {self.claim_id}>"