"""
Insurance Schemas
Pydantic models for insurance data validation
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID
from decimal import Decimal

from app.models.insurance import (
    InsuranceType,
    ClaimStatus,
    RelationshipToSubscriber,
)


# Insurance Carrier Schemas

class InsuranceCarrierBase(BaseModel):
    """Base insurance carrier schema"""
    name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    payer_id: Optional[str] = Field(None, max_length=50)
    edi_enabled: bool = False
    notes: Optional[str] = None
    is_active: bool = True


class InsuranceCarrierCreate(InsuranceCarrierBase):
    """Schema for creating insurance carrier"""
    pass


class InsuranceCarrierUpdate(BaseModel):
    """Schema for updating insurance carrier"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    fax: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    payer_id: Optional[str] = None
    edi_enabled: Optional[bool] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class InsuranceCarrierResponse(InsuranceCarrierBase):
    """Schema for insurance carrier response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InsuranceCarrierListResponse(BaseModel):
    """Schema for list of insurance carriers"""
    carriers: List[InsuranceCarrierResponse]
    count: int


# Patient Insurance Schemas

class PatientInsuranceBase(BaseModel):
    """Base patient insurance schema"""
    carrier_id: UUID
    insurance_type: InsuranceType = InsuranceType.PRIMARY
    subscriber_id: str = Field(..., min_length=1, max_length=50)
    group_number: Optional[str] = Field(None, max_length=50)
    relationship_to_subscriber: RelationshipToSubscriber = RelationshipToSubscriber.SELF
    subscriber_first_name: Optional[str] = Field(None, max_length=100)
    subscriber_last_name: Optional[str] = Field(None, max_length=100)
    subscriber_dob: Optional[date] = None
    subscriber_ssn: Optional[str] = Field(None, max_length=11)
    effective_date: Optional[date] = None
    termination_date: Optional[date] = None
    annual_maximum: Optional[Decimal] = Field(None, ge=0)
    annual_deductible: Optional[Decimal] = Field(None, ge=0)
    deductible_met: Decimal = Field(Decimal('0.0'), ge=0)
    preventive_coverage: int = Field(100, ge=0, le=100)
    basic_coverage: int = Field(80, ge=0, le=100)
    major_coverage: int = Field(50, ge=0, le=100)
    employer_name: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    is_active: bool = True


class PatientInsuranceCreate(PatientInsuranceBase):
    """Schema for creating patient insurance"""
    pass


class PatientInsuranceUpdate(BaseModel):
    """Schema for updating patient insurance"""
    carrier_id: Optional[UUID] = None
    insurance_type: Optional[InsuranceType] = None
    subscriber_id: Optional[str] = Field(None, min_length=1, max_length=50)
    group_number: Optional[str] = None
    relationship_to_subscriber: Optional[RelationshipToSubscriber] = None
    subscriber_first_name: Optional[str] = None
    subscriber_last_name: Optional[str] = None
    subscriber_dob: Optional[date] = None
    subscriber_ssn: Optional[str] = None
    effective_date: Optional[date] = None
    termination_date: Optional[date] = None
    annual_maximum: Optional[Decimal] = None
    annual_deductible: Optional[Decimal] = None
    deductible_met: Optional[Decimal] = None
    preventive_coverage: Optional[int] = Field(None, ge=0, le=100)
    basic_coverage: Optional[int] = Field(None, ge=0, le=100)
    major_coverage: Optional[int] = Field(None, ge=0, le=100)
    employer_name: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class PatientInsuranceResponse(PatientInsuranceBase):
    """Schema for patient insurance response"""
    id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PatientInsuranceListResponse(BaseModel):
    """Schema for list of patient insurance"""
    insurances: List[PatientInsuranceResponse]
    count: int


# Insurance Claim Schemas

class ProcedureCode(BaseModel):
    """Procedure code schema"""
    code: str
    description: str
    fee: Decimal


class InsuranceClaimBase(BaseModel):
    """Base insurance claim schema"""
    patient_insurance_id: UUID
    service_date: date
    billed_amount: Decimal = Field(..., gt=0)
    procedure_codes: List[ProcedureCode]
    diagnosis_codes: Optional[List[str]] = []
    notes: Optional[str] = None


class InsuranceClaimCreate(InsuranceClaimBase):
    """Schema for creating insurance claim"""
    pass


class InsuranceClaimUpdate(BaseModel):
    """Schema for updating insurance claim"""
    status: Optional[ClaimStatus] = None
    submission_date: Optional[date] = None
    received_date: Optional[date] = None
    paid_date: Optional[date] = None
    allowed_amount: Optional[Decimal] = Field(None, ge=0)
    deductible_amount: Optional[Decimal] = Field(None, ge=0)
    copay_amount: Optional[Decimal] = Field(None, ge=0)
    paid_amount: Optional[Decimal] = Field(None, ge=0)
    patient_responsibility: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    denial_reason: Optional[str] = None


class InsuranceClaimResponse(InsuranceClaimBase):
    """Schema for insurance claim response"""
    id: UUID
    practice_id: UUID
    patient_id: UUID
    carrier_id: UUID
    claim_number: str
    status: ClaimStatus
    submission_date: Optional[date]
    received_date: Optional[date]
    paid_date: Optional[date]
    allowed_amount: Optional[Decimal]
    deductible_amount: Decimal
    copay_amount: Decimal
    paid_amount: Decimal
    patient_responsibility: Decimal
    denial_reason: Optional[str]
    outstanding_balance: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InsuranceClaimListResponse(BaseModel):
    """Schema for list of insurance claims"""
    claims: List[InsuranceClaimResponse]
    count: int


# Pre-Authorization Schemas

class PreAuthorizationBase(BaseModel):
    """Base pre-authorization schema"""
    patient_insurance_id: UUID
    request_date: date
    procedure_codes: List[ProcedureCode]
    estimated_cost: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class PreAuthorizationCreate(PreAuthorizationBase):
    """Schema for creating pre-authorization"""
    pass


class PreAuthorizationUpdate(BaseModel):
    """Schema for updating pre-authorization"""
    status: Optional[str] = None
    approval_date: Optional[date] = None
    expiration_date: Optional[date] = None
    approved_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class PreAuthorizationResponse(PreAuthorizationBase):
    """Schema for pre-authorization response"""
    id: UUID
    patient_id: UUID
    authorization_number: str
    status: str
    approval_date: Optional[date]
    expiration_date: Optional[date]
    approved_amount: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PreAuthorizationListResponse(BaseModel):
    """Schema for list of pre-authorizations"""
    pre_authorizations: List[PreAuthorizationResponse]
    count: int

# Eligibility Schemas
class EligibilityResponse(BaseModel):
    """Schema for eligibility verification result"""
    id: UUID
    patient_id: UUID
    patient_insurance_id: UUID
    carrier_id: UUID
    verified_at: datetime
    is_active: bool
    coverage_status: Optional[str]
    remaining_benefits: Optional[Decimal]
    deductible_remaining: Optional[Decimal]
    notes: Optional[str]
    class Config:
        from_attributes = True

class EligibilityListResponse(BaseModel):
    """Schema for list of eligibility results"""
    eligibilities: List[EligibilityResponse]
    count: int

# Explanation of Benefits (EOB) Schemas
class ExplanationOfBenefitsResponse(BaseModel):
    """Schema for EOB"""
    id: UUID
    claim_id: UUID
    generated_at: datetime
    description: Optional[str]
    amount_covered: Optional[Decimal]
    amount_patient_responsibility: Optional[Decimal]
    class Config:
        from_attributes = True

class ExplanationOfBenefitsListResponse(BaseModel):
    """Schema for list of EOBs"""
    eobs: List[ExplanationOfBenefitsResponse]
    count: int


# Insurance Verification Schemas

class InsuranceVerificationRequest(BaseModel):
    """Schema for insurance verification request"""
    patient_insurance_id: UUID
    service_date: date


class InsuranceVerificationResponse(BaseModel):
    """Schema for insurance verification response"""
    is_active: bool
    coverage_status: str
    remaining_benefits: Optional[Decimal]
    deductible_remaining: Optional[Decimal]
    verification_date: datetime
    message: str