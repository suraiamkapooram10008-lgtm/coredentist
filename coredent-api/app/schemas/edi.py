"""
EDI Schemas
Insurance eligibility and claims request/response models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date


class EligibilityCheckRequest(BaseModel):
    """Request to check insurance eligibility"""
    patient_id: UUID
    patient_insurance_id: UUID
    service_date: Optional[date] = None


class EligibilityCheckResponse(BaseModel):
    """Response from eligibility check"""
    eligible: bool
    coverage_status: str
    plan_name: str
    effective_date: str
    termination_date: str
    copay: float
    deductible: float
    deductible_remaining: float
    coinsurance: float
    annual_max: float
    annual_remaining: float
    message: str


class ClaimProcedure(BaseModel):
    """Individual procedure in a claim"""
    procedure_code: str
    tooth: Optional[str] = None
    surface: Optional[str] = None
    fee: float
    date_of_service: date


class ClaimSubmitRequest(BaseModel):
    """Request to submit a dental claim"""
    patient_id: UUID
    patient_insurance_id: UUID
    procedures: List[ClaimProcedure]
    total_amount: float
    service_date: date
    diagnosis_codes: Optional[List[str]] = None


class ClaimSubmitResponse(BaseModel):
    """Response from claim submission"""
    claim_id: str
    external_claim_id: str
    status: str
    message: str
    submitted_at: str


class ClaimStatusResponse(BaseModel):
    """Response for claim status"""
    claim_id: str
    external_claim_id: str
    status: str
    paid_amount: float = 0
    patient_responsibility: float = 0
    denial_code: Optional[str] = None
    denial_reason: Optional[str] = None
    processed_date: Optional[str] = None
