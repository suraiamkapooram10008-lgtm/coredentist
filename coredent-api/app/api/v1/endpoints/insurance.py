"""
Insurance Endpoints
CRUD operations for insurance management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, date
from typing import List, Optional, Any
import json

from app.core.database import get_db
from app.api.deps import get_current_user
from app.core.edi import submit_dental_claim
from app.models.user import User
from app.models.insurance import (
    InsuranceCarrier,
    PatientInsurance,
    InsuranceClaim,
    InsurancePreAuthorization,
    ClaimStatus,
    Eligibility,
    ExplanationOfBenefits,
)
from app.models.patient import Patient
from app.schemas.insurance import (
    InsuranceCarrierCreate,
    InsuranceCarrierUpdate,
    InsuranceCarrierResponse,
    InsuranceCarrierListResponse,
    PatientInsuranceCreate,
    PatientInsuranceUpdate,
    PatientInsuranceResponse,
    PatientInsuranceListResponse,
    InsuranceClaimCreate,
    InsuranceClaimUpdate,
    InsuranceClaimResponse,
    InsuranceClaimListResponse,
    PreAuthorizationCreate,
    PreAuthorizationUpdate,
    PreAuthorizationResponse,
    PreAuthorizationListResponse,
    EligibilityListResponse,
    ExplanationOfBenefitsListResponse,
    InsuranceVerificationRequest,
    InsuranceVerificationResponse,
)
from app.api.deps import verify_csrf

router = APIRouter()


# Insurance Carrier Endpoints

@router.get("/carriers/", response_model=InsuranceCarrierListResponse)
async def list_carriers(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List insurance carriers
    """
    query = select(InsuranceCarrier)
    
    if is_active is not None:
        query = query.where(InsuranceCarrier.is_active == is_active)
    
    if search:
        query = query.where(InsuranceCarrier.name.ilike(f"%{search}%"))
    
    query = query.order_by(InsuranceCarrier.name)
    
    result = await db.execute(query)
    carriers = result.scalars().all()
    
    return InsuranceCarrierListResponse(
        carriers=carriers,
        count=len(carriers),
    )


@router.get("/carriers/{carrier_id}", response_model=InsuranceCarrierResponse)
async def get_carrier(
    carrier_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get insurance carrier by ID
    """
    result = await db.execute(
        select(InsuranceCarrier).where(InsuranceCarrier.id == carrier_id)
    )
    carrier = result.scalar_one_or_none()
    
    if not carrier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance carrier not found",
        )
    
    return carrier


@router.post("/carriers/", response_model=InsuranceCarrierResponse)
async def create_carrier(
    carrier_data: InsuranceCarrierCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new insurance carrier
    """
    # Check for duplicate payer_id
    if carrier_data.payer_id:
        result = await db.execute(
            select(InsuranceCarrier).where(InsuranceCarrier.payer_id == carrier_data.payer_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Carrier with this payer ID already exists",
            )
    
    carrier = InsuranceCarrier(**carrier_data.dict())
    db.add(carrier)
    await db.commit()
    await db.refresh(carrier)
    
    return carrier


@router.put("/carriers/{carrier_id}", response_model=InsuranceCarrierResponse)
async def update_carrier(
    carrier_id: str,
    carrier_data: InsuranceCarrierUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update insurance carrier
    """
    result = await db.execute(
        select(InsuranceCarrier).where(InsuranceCarrier.id == carrier_id)
    )
    carrier = result.scalar_one_or_none()
    
    if not carrier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance carrier not found",
        )
    
    update_data = carrier_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(carrier, field, value)
    
    await db.commit()
    await db.refresh(carrier)
    
    return carrier


# Patient Insurance Endpoints

@router.get("/patients/{patient_id}/policies", response_model=PatientInsuranceListResponse)
async def list_patient_insurance(
    patient_id: str,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List patient insurance policies
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    query = select(PatientInsurance).where(PatientInsurance.patient_id == patient_id)
    
    if is_active is not None:
        query = query.where(PatientInsurance.is_active == is_active)
    
    query = query.order_by(PatientInsurance.insurance_type)
    
    result = await db.execute(query)
    insurances = result.scalars().all()
    
    return PatientInsuranceListResponse(
        insurances=insurances,
        count=len(insurances),
    )


@router.post("/patients/{patient_id}/policies", response_model=PatientInsuranceResponse)
async def create_patient_insurance(
    patient_id: str,
    insurance_data: PatientInsuranceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Add insurance policy to patient
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Verify carrier exists
    result = await db.execute(
        select(InsuranceCarrier).where(InsuranceCarrier.id == insurance_data.carrier_id)
    )
    carrier = result.scalar_one_or_none()
    
    if not carrier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance carrier not found",
        )
    
    insurance = PatientInsurance(
        patient_id=patient_id,
        **insurance_data.dict()
    )
    
    db.add(insurance)
    await db.commit()
    await db.refresh(insurance)
    
    return insurance


@router.put("/policies/{policy_id}", response_model=PatientInsuranceResponse)
async def update_patient_insurance(
    policy_id: str,
    insurance_data: PatientInsuranceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update patient insurance policy
    """
    result = await db.execute(
        select(PatientInsurance).where(PatientInsurance.id == policy_id)
    )
    insurance = result.scalar_one_or_none()
    
    if not insurance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance policy not found",
        )
    
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == insurance.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    update_data = insurance_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(insurance, field, value)
    
    await db.commit()
    await db.refresh(insurance)
    
    return insurance


@router.delete("/policies/{policy_id}")
async def delete_patient_insurance(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete patient insurance policy
    """
    result = await db.execute(
        select(PatientInsurance).where(PatientInsurance.id == policy_id)
    )
    insurance = result.scalar_one_or_none()
    
    if not insurance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance policy not found",
        )
    
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == insurance.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    await db.delete(insurance)
    await db.commit()
    
    return {"message": "Insurance policy deleted successfully"}


# Insurance Claim Endpoints

@router.get("/claims/", response_model=InsuranceClaimListResponse)
async def list_claims(
    status: Optional[ClaimStatus] = Query(None, description="Filter by status"),
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List insurance claims
    """
    query = select(InsuranceClaim).where(InsuranceClaim.practice_id == current_user.practice_id)
    
    if status:
        query = query.where(InsuranceClaim.status == status)
    
    if patient_id:
        query = query.where(InsuranceClaim.patient_id == patient_id)
    
    if start_date:
        query = query.where(InsuranceClaim.service_date >= start_date)
    
    if end_date:
        query = query.where(InsuranceClaim.service_date <= end_date)
    
    query = query.order_by(InsuranceClaim.service_date.desc())
    
    result = await db.execute(query)
    claims = result.scalars().all()
    
    return InsuranceClaimListResponse(
        claims=claims,
        count=len(claims),
    )


@router.post("/claims/", response_model=InsuranceClaimResponse)
async def create_claim(
    claim_data: InsuranceClaimCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create insurance claim
    """
    # Get patient insurance
    result = await db.execute(
        select(PatientInsurance).where(PatientInsurance.id == claim_data.patient_insurance_id)
    )
    patient_insurance = result.scalar_one_or_none()
    
    if not patient_insurance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insurance not found",
        )
    
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_insurance.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Generate claim number
    today = datetime.now()
    claim_count = await db.execute(
        select(func.count(InsuranceClaim.id)).where(
            InsuranceClaim.practice_id == current_user.practice_id,
            func.date(InsuranceClaim.created_at) == today.date()
        )
    )
    count = claim_count.scalar() or 0
    
    claim_number = f"CLM-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    
    # Convert procedure codes to JSON string
    procedure_codes_json = json.dumps([pc.dict() for pc in claim_data.procedure_codes])
    diagnosis_codes_json = json.dumps(claim_data.diagnosis_codes or [])
    
    claim = InsuranceClaim(
        practice_id=current_user.practice_id,
        patient_id=patient_insurance.patient_id,
        patient_insurance_id=claim_data.patient_insurance_id,
        carrier_id=patient_insurance.carrier_id,
        claim_number=claim_number,
        service_date=claim_data.service_date,
        billed_amount=claim_data.billed_amount,
        procedure_codes=procedure_codes_json,
        diagnosis_codes=diagnosis_codes_json,
        notes=claim_data.notes,
    )
    
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    
    return claim


@router.put("/claims/{claim_id}", response_model=InsuranceClaimResponse)
async def update_claim(
    claim_id: str,
    claim_data: InsuranceClaimUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update insurance claim
    """
    result = await db.execute(
        select(InsuranceClaim).where(
            InsuranceClaim.id == claim_id,
            InsuranceClaim.practice_id == current_user.practice_id,
        )
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )
    
    update_data = claim_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(claim, field, value)
    
    await db.commit()
    await db.refresh(claim)
    
    return claim


@router.post("/claims/{claim_id}/submit")
async def submit_claim(
    claim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Submit claim to insurance
    """
    result = await db.execute(
        select(InsuranceClaim).where(
            InsuranceClaim.id == claim_id,
            InsuranceClaim.practice_id == current_user.practice_id,
        )
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )
    
    # Update claim status
    claim.status = ClaimStatus.SUBMITTED
    claim.submission_date = datetime.now().date()
    
    # Integrate with EDI clearinghouse for electronic submission
    try:
        # Get patient and insurance data for EDI
        result = await db.execute(
            select(Patient).where(Patient.id == claim.patient_id)
        )
        patient = result.scalar_one_or_none()
        
        result = await db.execute(
            select(PatientInsurance).where(PatientInsurance.id == claim.patient_insurance_id)
        )
        patient_insurance = result.scalar_one_or_none()
        
        if patient and patient_insurance:
            # Prepare patient data
            patient_data = {
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "address": patient.address,
                "city": patient.city,
                "state": patient.state,
                "zip_code": patient.zip_code,
            }
            
            # Prepare subscriber data
            subscriber_data = {
                "member_id": patient_insurance.member_id,
                "group_number": patient_insurance.group_number,
                "subscriber_name": f"{patient.first_name} {patient.last_name}",
            }
            
            # Prepare provider data
            provider_data = {
                "npi": current_user.npi or "1234567890",
                "tax_id": "123456789",
            }
            
            # Parse procedure codes
            import json
            procedure_codes = json.loads(claim.procedure_codes) if claim.procedure_codes else []
            
            # Prepare claim lines
            claim_lines = []
            for proc in procedure_codes:
                claim_lines.append({
                    "procedure_code": proc.get("code"),
                    "tooth": proc.get("tooth"),
                    "surface": proc.get("surface"),
                    "charge": float(proc.get("fee", 0)),
                })
            
            # Submit via EDI
            edi_result = await submit_dental_claim(
                patient_data=patient_data,
                subscriber_data=subscriber_data,
                provider_data=provider_data,
                claim_lines=claim_lines,
                claim_number=claim.claim_number,
            )
            
            # Update claim with confirmation number
            if edi_result.get("confirmation_number"):
                claim.confirmation_number = edi_result["confirmation_number"]
    
    except Exception as e:
        # Log error but don't fail - claim is still submitted
        import logging
        logging.warning(f"EDI submission failed: {str(e)}")
    
    await db.commit()
    
    return {"message": "Claim submitted successfully", "claim_number": claim.claim_number}


# Pre-Authorization Endpoints

# New Endpoints for Eligibility
@router.get("/eligibility/", response_model=EligibilityListResponse)
async def list_eligibility(
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List eligibility records for the current practice
    """
    query = select(Eligibility)
    if patient_id:
        query = query.where(Eligibility.patient_id == patient_id)
    result = await db.execute(query)
    eligibilities = result.scalars().all()
    filtered = []
    for e in eligibilities:
        result = await db.execute(
            select(Patient).where(
                Patient.id == e.patient_id,
                Patient.practice_id == current_user.practice_id,
            )
        )
        patient = result.scalar_one_or_none()
        if patient:
            filtered.append(e)
    return EligibilityListResponse(
        eligibilities=filtered,
        count=len(filtered),
    )

# New Endpoints for Explanation of Benefits (EOB)
@router.get("/eobs/", response_model=ExplanationOfBenefitsListResponse)
async def list_eobs(
    claim_id: Optional[str] = Query(None, description="Filter by claim"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List Explanation of Benefits for the current practice
    """
    query = select(ExplanationOfBenefits)
    if claim_id:
        query = query.where(ExplanationOfBenefits.claim_id == claim_id)
    result = await db.execute(query)
    eobs = result.scalars().all()
    filtered = []
    for eob in eobs:
        # Verify claim belongs to practice
        result = await db.execute(
            select(InsuranceClaim).where(
                InsuranceClaim.id == eob.claim_id,
                InsuranceClaim.practice_id == current_user.practice_id,
            )
        )
        claim = result.scalar_one_or_none()
        if claim:
            filtered.append(eob)
    return ExplanationOfBenefitsListResponse(
        eobs=filtered,
        count=len(filtered),
    )

@router.get("/pre-auth/", response_model=PreAuthorizationListResponse)
async def list_pre_authorizations(
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List pre-authorizations
    """
    query = select(InsurancePreAuthorization)
    
    if patient_id:
        query = query.where(InsurancePreAuthorization.patient_id == patient_id)
    
    if status:
        query = query.where(InsurancePreAuthorization.status == status)
    
    query = query.order_by(InsurancePreAuthorization.request_date.desc())
    
    result = await db.execute(query)
    pre_auths = result.scalars().all()
    
    # Filter by practice (through patient)
    filtered_pre_auths = []
    for pre_auth in pre_auths:
        result = await db.execute(
            select(Patient).where(
                Patient.id == pre_auth.patient_id,
                Patient.practice_id == current_user.practice_id,
            )
        )
        if result.scalar_one_or_none():
            filtered_pre_auths.append(pre_auth)
    
    return PreAuthorizationListResponse(
        pre_authorizations=filtered_pre_auths,
        count=len(filtered_pre_auths),
    )


@router.post("/pre-auth/", response_model=PreAuthorizationResponse)
async def create_pre_authorization(
    pre_auth_data: PreAuthorizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create pre-authorization request
    """
    # Get patient insurance
    result = await db.execute(
        select(PatientInsurance).where(PatientInsurance.id == pre_auth_data.patient_insurance_id)
    )
    patient_insurance = result.scalar_one_or_none()
    
    if not patient_insurance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient insurance not found",
        )
    
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_insurance.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Generate authorization number
    today = datetime.now()
    auth_number = f"PA-{today.strftime('%Y%m%d')}-{patient_insurance.patient_id[:8]}"
    
    # Convert procedure codes to JSON string
    procedure_codes_json = json.dumps([pc.dict() for pc in pre_auth_data.procedure_codes])
    
    pre_auth = InsurancePreAuthorization(
        patient_id=patient_insurance.patient_id,
        patient_insurance_id=pre_auth_data.patient_insurance_id,
        authorization_number=auth_number,
        request_date=pre_auth_data.request_date,
        procedure_codes=procedure_codes_json,
        estimated_cost=pre_auth_data.estimated_cost,
        notes=pre_auth_data.notes,
    )
    
    db.add(pre_auth)
    await db.commit()
    await db.refresh(pre_auth)
    
    return pre_auth


@router.put("/pre-auth/{pre_auth_id}", response_model=PreAuthorizationResponse)
async def update_pre_authorization(
    pre_auth_id: str,
    pre_auth_data: PreAuthorizationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update pre-authorization
    """
    result = await db.execute(
        select(InsurancePreAuthorization).where(InsurancePreAuthorization.id == pre_auth_id)
    )
    pre_auth = result.scalar_one_or_none()
    
    if not pre_auth:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pre-authorization not found",
        )
    
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == pre_auth.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    update_data = pre_auth_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pre_auth, field, value)
    
    await db.commit()
    await db.refresh(pre_auth)
    
    return pre_auth