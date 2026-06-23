"""
EDI Schemas
Insurance eligibility and claims request/response models
"""

from pydantic import BaseModel
from typing import Optional, List, Union
from uuid import UUID
from datetime import date


class EligibilityCheckRequest(BaseModel):
    """Request to check insurance eligibility"""
    patient_id: UUID
    patient_insurance_id: UUID
    service_date: Optional[date] = None


class EligibilityCheckResponse(BaseModel):
    """Response from eligibility check.

    Fields beyond the core `eligible`/`coverage_status` flags are all optional
    because real-world clearinghouse responses (especially for terminated or
    error states) return partial payloads.
    """
    eligible: bool
    coverage_status: str
    plan_name: Optional[str] = None
    effective_date: Optional[str] = None
    termination_date: Optional[str] = None
    copay: Optional[float] = None
    deductible: Optional[float] = None
    deductible_remaining: Optional[float] = None
    coinsurance: Optional[float] = None
    annual_max: Optional[float] = None
    annual_remaining: Optional[float] = None
    message: Optional[str] = None
    error: Optional[str] = None


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
    """Response from claim submission. Supports accept/reject paths."""
    status: str
    claim_id: Optional[Union[UUID, str]] = None
    external_claim_id: Optional[str] = None
    submitted_at: Optional[str] = None
    message: Optional[str] = None


class ClaimStatusResponse(BaseModel):
    """Response for claim status. Tolerant of partial/missing fields."""
    status: str
    claim_id: Optional[Union[UUID, str]] = None
    external_claim_id: Optional[str] = None
    paid_amount: float = 0
    patient_responsibility: float = 0
    denial_code: Optional[str] = None
    denial_reason: Optional[str] = None
    processed_date: Optional[Union[date, str]] = None
    message: Optional[str] = None
