"""
Insurance Endpoints
CRUD operations for insurance management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
from typing import Optional
from uuid import UUID
import json
import httpx

from app.core.database import get_db
from app.core.config_simple import settings
from app.models.user import User, UserRole
from app.api.deps import get_current_user, require_role, verify_csrf
from app.core.audit import log_audit_event
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
) -> InsuranceCarrierListResponse:
    """
    List insurance carriers
    """
    query = select(InsuranceCarrier)

    if is_active is not None:
        query = query.where(InsuranceCarrier.is_active == is_active)

    if search:
        # Use parameterized query to prevent SQL injection
        search_pattern = f"%{search}%"
        query = query.where(InsuranceCarrier.name.ilike(search_pattern))

    query = query.order_by(InsuranceCarrier.name)

    result = await db.execute(query)
    carriers = result.scalars().all()

    return InsuranceCarrierListResponse(
        carriers=carriers,
        count=len(carriers),
    )


@router.get("/carriers/{carrier_id}", response_model=InsuranceCarrierResponse)
async def get_carrier(
    carrier_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InsuranceCarrierResponse:
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
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> InsuranceCarrierResponse:
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
    carrier_id: UUID,
    carrier_data: InsuranceCarrierUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> InsuranceCarrierResponse:
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
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientInsuranceListResponse:
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

    # HIPAA: Log patient insurance access
    await log_audit_event(
        db, current_user, "list_patient_insurance", "patient", patient_id, request
    )
    await db.commit()

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
) -> PatientInsuranceResponse:
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
) -> PatientInsuranceResponse:
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
) -> PatientInsuranceResponse:
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
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InsuranceClaimListResponse:
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

    # HIPAA: Log claim list access
    await log_audit_event(
        db, current_user, "list_insurance_claims", "insurance_claim", None, request
    )
    await db.commit()

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
) -> InsuranceClaimResponse:
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

    claim = InsuranceClaim(
        practice_id=current_user.practice_id,
        patient_id=patient_insurance.patient_id,
        patient_insurance_id=claim_data.patient_insurance_id,
        carrier_id=patient_insurance.carrier_id,
        claim_number=claim_number,
        service_date=claim_data.service_date,
        billed_amount=claim_data.billed_amount,
        procedure_codes=[pc.model_dump(mode='json') for pc in claim_data.procedure_codes],
        diagnosis_codes=(claim_data.diagnosis_codes or []),
        notes=claim_data.notes,
    )

    db.add(claim)
    await db.commit()
    await db.refresh(claim)

    return claim


@router.put("/claims/{claim_id}", response_model=InsuranceClaimResponse)
async def update_claim(
    claim_id: UUID,
    claim_data: InsuranceClaimUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> InsuranceClaimResponse:
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
    claim_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> InsuranceClaimResponse:
    """Submit an existing draft claim through DentalXChange.

    The claim is marked submitted only after the clearinghouse returns a
    non-empty external claim ID. Provider and network failures leave the claim
    unchanged so the UI cannot report a false submission.
    """
    if not settings.DXC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claims submission service not configured",
        )

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

    patient_result = await db.execute(
        select(Patient).where(
            Patient.id == claim.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = patient_result.scalar_one_or_none()
    insurance_result = await db.execute(
        select(PatientInsurance).where(
            PatientInsurance.id == claim.patient_insurance_id,
            PatientInsurance.patient_id == claim.patient_id,
        )
    )
    patient_insurance = insurance_result.scalar_one_or_none()
    carrier_result = await db.execute(
        select(InsuranceCarrier).where(InsuranceCarrier.id == claim.carrier_id)
    )
    carrier = carrier_result.scalar_one_or_none()

    if not patient or not patient_insurance or not carrier:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Claim is missing required patient or insurance data",
        )
    if not carrier.edi_enabled or not carrier.payer_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Insurance carrier is not configured for electronic claims",
        )

    procedure_codes = claim.procedure_codes or []
    if isinstance(procedure_codes, str):
        procedure_codes = json.loads(procedure_codes)
    procedures = [
        {
            "procedureCode": procedure.get("code"),
            "tooth": procedure.get("tooth"),
            "surface": procedure.get("surface"),
            "fee": float(procedure.get("fee", 0)),
            "dateOfService": claim.service_date.isoformat(),
        }
        for procedure in procedure_codes
    ]
    payload = {
        "claim": {
            "clientClaimId": claim.claim_number,
            "patientFirstName": patient.first_name,
            "patientLastName": patient.last_name,
            "patientDateOfBirth": patient.date_of_birth.isoformat() if patient.date_of_birth else "",
            "subscriberId": patient_insurance.subscriber_id,
            "groupNumber": patient_insurance.group_number or "",
            "payerId": carrier.payer_id,
            "providerNpi": getattr(current_user, "npi", "") or "",
            "procedures": procedures,
            "totalAmount": float(claim.billed_amount),
            "diagnosisCodes": claim.diagnosis_codes or [],
        }
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.DXC_BASE_URL}/claims",
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.DXC_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
    except httpx.RequestError as exc:
        await log_audit_event(
            db,
            current_user,
            "submit_claim_failed",
            "insurance_claim",
            claim.id,
            request,
            {"reason": "provider_unavailable"},
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claims provider is unavailable",
        ) from exc

    if response.status_code not in (200, 201):
        await log_audit_event(
            db,
            current_user,
            "submit_claim_failed",
            "insurance_claim",
            claim.id,
            request,
            {"reason": "provider_rejected", "status_code": response.status_code},
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Claims provider rejected the submission",
        )

    try:
        provider_data = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Claims provider returned an invalid response",
        ) from exc

    external_claim_id = provider_data.get("claimId")
    if not external_claim_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Claims provider did not confirm submission",
        )

    claim.status = ClaimStatus.SUBMITTED
    claim.submission_date = datetime.now().date()
    claim.edi_transaction_id = str(external_claim_id)
    claim.confirmation_number = str(
        provider_data.get("confirmationNumber") or external_claim_id
    )

    await log_audit_event(
        db, current_user, "submit_insurance_claim", "insurance_claim", claim.id, request
    )
    await db.commit()
    await db.refresh(claim)
    return claim


# Pre-Authorization Endpoints

# New Endpoints for Eligibility
@router.get("/eligibility/", response_model=EligibilityListResponse)
async def list_eligibility(
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> EligibilityListResponse:
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

    # HIPAA: Log eligibility access
    await log_audit_event(
        db, current_user, "list_eligibility", "eligibility", None, request
    )
    await db.commit()

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
    request: Request = None,
) -> ExplanationOfBenefitsListResponse:
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

    # HIPAA: Log EOB access
    await log_audit_event(
        db, current_user, "list_eobs", "eob", None, request
    )
    await db.commit()

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
    request: Request = None,
) -> PreAuthorizationListResponse:
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

    # HIPAA: Log pre-auth access
    await log_audit_event(
        db, current_user, "list_pre_authorizations", "pre_authorization", None, request
    )
    await db.commit()

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
) -> PreAuthorizationResponse:
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
        procedure_codes=procedure_codes_json,
        estimated_cost=pre_auth_data.estimated_cost,
        notes=pre_auth_data.notes,
    )

    db.add(pre_auth)
    await db.commit()
    await db.refresh(pre_auth)

    return pre_auth


# Fee Schedule Endpoints

from app.models.insurance import FeeSchedule, FeeScheduleEntry
from app.schemas.insurance import FeeScheduleCreate, FeeScheduleResponse, FeeScheduleListResponse

@router.get("/fee-schedules/", response_model=FeeScheduleListResponse)
async def list_fee_schedules(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> FeeScheduleListResponse:
    """
    List fee schedules for the practice
    """
    query = select(FeeSchedule).where(FeeSchedule.practice_id == current_user.practice_id)
    if is_active is not None:
        query = query.where(FeeSchedule.is_active == is_active)

    result = await db.execute(query)
    fee_schedules = result.scalars().all()

    # HIPAA Audit log mapping
    await log_audit_event(
        db, current_user, "list_fee_schedules", "fee_schedule", None, request
    )
    await db.commit()

    return FeeScheduleListResponse(
        fee_schedules=fee_schedules,
        count=len(fee_schedules)
    )

@router.post("/fee-schedules/", response_model=FeeScheduleResponse)
async def create_fee_schedule(
    schedule_data: FeeScheduleCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> FeeScheduleResponse:
    """
    Create a new fee schedule
    """
    new_schedule = FeeSchedule(
        practice_id=current_user.practice_id,
        name=schedule_data.name,
        description=schedule_data.description,
        is_active=schedule_data.is_active,
    )
    db.add(new_schedule)
    await db.flush()

    if schedule_data.entries:
        for entry_data in schedule_data.entries:
            entry = FeeScheduleEntry(
                fee_schedule_id=new_schedule.id,
                **entry_data.dict()
            )
            db.add(entry)

    await db.commit()
    await db.refresh(new_schedule)
    return new_schedule


@router.put("/pre-auth/{pre_auth_id}", response_model=PreAuthorizationResponse)
async def update_pre_authorization(
    pre_auth_id: str,
    pre_auth_data: PreAuthorizationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> PreAuthorizationResponse:
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