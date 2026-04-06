"""
Insurance EDI Endpoints
DentalXChange integration for eligibility and claims
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Any
from uuid import UUID
from datetime import datetime, timedelta, timezone
import requests
import json
import secrets
import string

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.insurance import PatientInsurance, InsuranceClaim, ClaimStatus
from app.models.patient import Patient
from app.core.audit import log_audit_event
from app.api.deps import get_current_user, verify_csrf
from app.schemas.edi import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    ClaimSubmitRequest,
    ClaimSubmitResponse,
    ClaimStatusResponse,
)

router = APIRouter()


def generate_confirmation_code() -> str:
    """Generate a unique confirmation code"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))


def _get_dxc_headers() -> dict:
    """Get headers for DentalXChange API"""
    return {
        "Authorization": f"Bearer {settings.DXC_API_KEY}",
        "Content-Type": "application/json",
    }


@router.post("/eligibility/check", response_model=EligibilityCheckResponse)
async def check_eligibility(
    request: Request,
    eligibility_data: EligibilityCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Check patient insurance eligibility in real-time.
    
    Design decisions:
    - Source of truth: DentalXChange API
    - Derived: Eligibility status from payer response
    - Stored: Check history in database (optional)
    """
    if not settings.DXC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Insurance verification service not configured",
        )
    
    # Verify patient insurance exists
    result = await db.execute(
        select(PatientInsurance).where(
            PatientInsurance.id == eligibility_data.patient_insurance_id,
            PatientInsurance.patient_id == eligibility_data.patient_id,
        )
    )
    insurance = result.scalar_one_or_none()
    
    if not insurance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insurance not found",
        )
    
    # Get patient details
    result = await db.execute(
        select(Patient).where(
            Patient.id == eligibility_data.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Build eligibility request payload
    payload = {
        "payerId": insurance.payer_id,
        "subscriberId": insurance.subscriber_id,
        "providerNpi": current_user.npi or "1234567890",
        "serviceDate": eligibility_data.service_date.isoformat() if eligibility_data.service_date else "",
        "serviceTypeCodes": ["30"],  # Health benefit plan coverage
        "patient": {
            "firstName": patient.first_name,
            "lastName": patient.last_name,
            "dateOfBirth": patient.date_of_birth.isoformat() if patient.date_of_birth else "",
            "memberId": insurance.subscriber_id,
        }
    }
    
    try:
        response = requests.post(
            f"{settings.DXC_BASE_URL}/eligibility",
            json=payload,
            headers=_get_dxc_headers(),
            timeout=30,
        )
        
        if response.status_code == 200:
            data = response.json()
            return EligibilityCheckResponse(
                eligible=data.get("eligible", False),
                coverage_status=data.get("coverageStatus", "Unknown"),
                plan_name=data.get("planName", ""),
                effective_date=data.get("effectiveDate", ""),
                termination_date=data.get("terminationDate", ""),
                copay=data.get("copay", 0),
                deductible=data.get("deductible", 0),
                deductible_remaining=data.get("deductibleRemaining", 0),
                coinsurance=data.get("coinsurance", 0),
                annual_max=data.get("annualMaximum", 0),
                annual_remaining=data.get("annualMaximumRemaining", 0),
                message=data.get("message", ""),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Eligibility check failed: {response.text}",
            )
            
    except requests.RequestException as e:
        # HIPAA: Log failed eligibility check (still an access attempt)
        await log_audit_event(
            db, current_user, "check_eligibility_failed", "patient", patient.id, request, {"error": str(e)}
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to verify eligibility: {str(e)}",
        )
    
    # HIPAA: Log successful eligibility check
    await log_audit_event(
        db, current_user, "check_eligibility_success", "patient", patient.id, request
    )
    await db.commit()


@router.post("/claims/submit", response_model=ClaimSubmitResponse)
async def submit_claim(
    request: Request,
    claim_data: ClaimSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Submit dental claim electronically to insurance.
    
    Design decisions:
    - Source of truth: DentalXChange API (returns claim ID)
    - Stored: Claim record in database with status tracking
    """
    if not settings.DXC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claims submission service not configured",
        )
    
    # Expert Hardening: Strictly verify insurance ownership to prevent 'Pivot ID Injection'
    result = await db.execute(
        select(PatientInsurance).join(Patient).where(
            PatientInsurance.id == claim_data.patient_insurance_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    insurance = result.scalar_one_or_none()
    
    if not insurance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valid patient insurance not found for your practice",
        )
    
    # Expert Hardening: Anti-Fraud Idempotency (Prevent Duplicate Submission)
    # Check if we submitted this exact procedure list for this patient in last 5 mins
    idempotency_window = datetime.now(timezone.utc) - timedelta(minutes=5)
    result = await db.execute(
        select(InsuranceClaim).where(
            InsuranceClaim.patient_id == claim_data.patient_id,
            InsuranceClaim.practice_id == current_user.practice_id,
            InsuranceClaim.created_at >= idempotency_window,
        )
    )
    recent_claims = result.scalars().all()
    # (Simplified procedure check: just check for ANY claim for this patient in last 5 min)
    if recent_claims:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A claim for this patient was recently submitted. Please wait 5 minutes to prevent duplicate billing."
        )
    
    # Get patient
    result = await db.execute(
        select(Patient).where(
            Patient.id == claim_data.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Build claim payload (837D format via JSON API)
    procedures = []
    for proc in claim_data.procedures:
        procedures.append({
            "procedureCode": proc.procedure_code,
            "tooth": proc.tooth,
            "surface": proc.surface,
            "fee": proc.fee,
            "dateOfService": proc.date_of_service.isoformat(),
        })
    
    payload = {
        "claim": {
            "patientFirstName": patient.first_name,
            "patientLastName": patient.last_name,
            "patientDateOfBirth": patient.date_of_birth.isoformat() if patient.date_of_birth else "",
            "subscriberId": insurance.subscriber_id,
            "payerId": insurance.payer_id,
            "providerNpi": current_user.npi or "1234567890",
            "providerName": f"{current_user.first_name} {current_user.last_name}",
            "serviceFacilityNpi": current_user.practice.npi if current_user.practice else "",
            "procedures": procedures,
            "totalAmount": claim_data.total_amount,
            "diagnosisCodes": claim_data.diagnosis_codes or [],
        }
    }
    
    try:
        response = requests.post(
            f"{settings.DXC_BASE_URL}/claims",
            json=payload,
            headers=_get_dxc_headers(),
            timeout=60,
        )
        
        if response.status_code in (200, 201):
            data = response.json()
            
            claim = InsuranceClaim(
                practice_id=current_user.practice_id,
                patient_id=patient.id,
                patient_insurance_id=insurance.id,
                carrier_id=insurance.carrier_id,
                claim_number=data.get("claimId", generate_confirmation_code()),
                status=ClaimStatus.SUBMITTED,
                billed_amount=claim_data.total_amount,
                service_date=claim_data.service_date,
                diagnosis_codes=json.dumps(claim_data.diagnosis_codes) if claim_data.diagnosis_codes else "[]",
                procedure_codes=json.dumps(procedures),
            )
            db.add(claim)
            await db.commit()
            await db.refresh(claim)
            
            # HIPAA: Log successful claim submission
            await log_audit_event(
                db, current_user, "submit_claim_success", "insurance_claim", claim.id, request
            )
            await db.commit()
            
            return ClaimSubmitResponse(
                claim_id=str(claim.id),
                external_claim_id=data.get("claimId", ""),
                status="submitted",
                message="Claim submitted successfully",
                submitted_at=data.get("submittedAt", ""),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Claim submission failed: {response.text}",
            )
            
    except requests.RequestException as e:
        # HIPAA: Log failed claim submission
        await log_audit_event(
            db, current_user, "submit_claim_failed", "patient", patient.id, request, {"error": str(e)}
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to submit claim: {str(e)}",
        )


@router.get("/claims/{claim_id}/status", response_model=ClaimStatusResponse)
async def get_claim_status(
    request: Request,
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get the status of a submitted claim.
    """
    if not settings.DXC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claims service not configured",
        )
    
    # Get claim from database
    result = await db.execute(
        select(InsuranceClaim).where(
            InsuranceClaim.id == UUID(claim_id),
        )
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )
    
    # Verify ownership
    result = await db.execute(
        select(Patient).where(
            Patient.id == claim.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )
    
    # HIPAA: Log claim status read (PHI read)
    await log_audit_event(
        db, current_user, "view_claim_status", "insurance_claim", claim.id, request
    )
    await db.commit()
    
    # Query DentalXChange for status
    try:
        response = requests.get(
            f"{settings.DXC_BASE_URL}/claims/{claim.claim_number}/status",
            headers=_get_dxc_headers(),
            timeout=30,
        )
        
        if response.status_code == 200:
            data = response.json()
            return ClaimStatusResponse(
                claim_id=str(claim.id),
                external_claim_id=claim.claim_number,
                status=data.get("status", claim.status.value),
                paid_amount=data.get("paidAmount", 0),
                patient_responsibility=data.get("patientResponsibility", 0),
                denial_code=data.get("denialCode"),
                denial_reason=data.get("denialReason"),
                processed_date=data.get("processedDate"),
            )
        else:
            # Return database status if API fails
            return ClaimStatusResponse(
                claim_id=str(claim.id),
                external_claim_id=claim.claim_number,
                status=claim.status.value,
            )
            
    except requests.RequestException:
        # Return database status if API unavailable
        return ClaimStatusResponse(
            claim_id=str(claim.id),
            external_claim_id=claim.claim_number,
            status=claim.status.value,
        )
