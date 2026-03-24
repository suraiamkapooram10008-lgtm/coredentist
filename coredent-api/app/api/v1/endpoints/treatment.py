"""
Treatment Planning Endpoints
CRUD operations for treatment planning
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from datetime import datetime, date
from typing import List, Optional, Any
import json
import uuid as uuid_lib

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.treatment import (
    TreatmentPlan,
    TreatmentPhase,
    TreatmentProcedure,
    ProcedureLibrary,
    TreatmentPlanTemplate,
    TreatmentPlanNote,
    TreatmentPlanStatus,
    ProcedureType,
)
from app.models.patient import Patient
from app.models.practice import Practice
from app.models.insurance import PatientInsurance, InsurancePreAuthorization
from app.schemas.treatment import (
    TreatmentPlanCreate,
    TreatmentPlanUpdate,
    TreatmentPlanResponse,
    TreatmentPlanListResponse,
    TreatmentPhaseCreate,
    TreatmentPhaseUpdate,
    TreatmentPhaseResponse,
    TreatmentPhaseListResponse,
    TreatmentProcedureCreate,
    TreatmentProcedureUpdate,
    TreatmentProcedureResponse,
    TreatmentProcedureListResponse,
    ProcedureLibraryCreate,
    ProcedureLibraryUpdate,
    ProcedureLibraryResponse,
    ProcedureLibraryListResponse,
    TreatmentPlanTemplateCreate,
    TreatmentPlanTemplateUpdate,
    TreatmentPlanTemplateResponse,
    TreatmentPlanTemplateListResponse,
    TreatmentPlanNoteCreate,
    TreatmentPlanNoteUpdate,
    TreatmentPlanNoteResponse,
    TreatmentPlanNoteListResponse,
    CostEstimateRequest,
    CostEstimateResponse,
    PlanAcceptanceRequest,
    PlanAcceptanceResponse,
    VisualBuilderConfig,
    VisualBuilderResponse,
)
from app.api.deps import verify_csrf

router = APIRouter()


# Treatment Plan Endpoints

@router.get("/plans/", response_model=TreatmentPlanListResponse)
async def list_treatment_plans(
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    status: Optional[TreatmentPlanStatus] = Query(None, description="Filter by status"),
    provider_id: Optional[str] = Query(None, description="Filter by provider"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List treatment plans for the current practice
    """
    query = select(TreatmentPlan).where(TreatmentPlan.practice_id == current_user.practice_id)
    
    if patient_id:
        query = query.where(TreatmentPlan.patient_id == patient_id)
    
    if status:
        query = query.where(TreatmentPlan.status == status)
    
    if provider_id:
        query = query.where(TreatmentPlan.provider_id == provider_id)
    
    if start_date:
        query = query.where(TreatmentPlan.created_date >= start_date)
    
    if end_date:
        query = query.where(TreatmentPlan.created_date <= end_date)
    
    query = query.order_by(TreatmentPlan.created_date.desc())
    
    result = await db.execute(query)
    plans = result.scalars().all()
    
    return TreatmentPlanListResponse(
        plans=plans,
        count=len(plans),
    )


@router.get("/patients/{patient_id}/plans", response_model=TreatmentPlanListResponse)
async def list_patient_treatment_plans(
    patient_id: str,
    status: Optional[TreatmentPlanStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List treatment plans for a specific patient
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
    
    query = select(TreatmentPlan).where(
        TreatmentPlan.patient_id == patient_id,
        TreatmentPlan.practice_id == current_user.practice_id,
    )
    
    if status:
        query = query.where(TreatmentPlan.status == status)
    
    query = query.order_by(TreatmentPlan.created_date.desc())
    
    result = await db.execute(query)
    plans = result.scalars().all()
    
    return TreatmentPlanListResponse(
        plans=plans,
        count=len(plans),
    )

@router.post("/plans/", response_model=TreatmentPlanResponse)
async def create_treatment_plan(
    plan_data: TreatmentPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new treatment plan
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == plan_data.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Verify provider belongs to practice
    result = await db.execute(
        select(User).where(
            User.id == plan_data.provider_id,
            User.practice_id == current_user.practice_id,
        )
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )
    
    plan = TreatmentPlan(
        practice_id=current_user.practice_id,
        **plan_data.dict()
    )
    
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    
    return plan


@router.get("/plans/{plan_id}", response_model=TreatmentPlanResponse)
async def get_treatment_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get treatment plan by ID
    """
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment plan not found",
        )
    
    return plan


@router.put("/plans/{plan_id}", response_model=TreatmentPlanResponse)
async def update_treatment_plan(
    plan_id: str,
    plan_data: TreatmentPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update treatment plan
    """
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment plan not found",
        )
    
    update_data = plan_data.dict(exclude_unset=True)
    
    # Handle status changes
    if 'status' in update_data:
        new_status = update_data['status']
        if new_status == TreatmentPlanStatus.PRESENTED and not plan.presented_date:
            plan.presented_date = datetime.now().date()
        elif new_status == TreatmentPlanStatus.ACCEPTED and not plan.accepted_date:
            plan.accepted_date = datetime.now().date()
    
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    await db.commit()
    await db.refresh(plan)
    
    return plan


@router.delete("/plans/{plan_id}")
async def delete_treatment_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete treatment plan (soft delete via status change)
    """
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment plan not found",
        )
    
    # Soft delete by changing status
    plan.status = TreatmentPlanStatus.CANCELLED
    
    await db.commit()
    
    return {"message": "Treatment plan cancelled successfully"}


# Treatment Phase Endpoints

@router.get("/plans/{plan_id}/phases", response_model=TreatmentPhaseListResponse)
async def list_treatment_phases(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List phases for a treatment plan
    """
    # Verify plan belongs to practice
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment plan not found",
        )
    
    query = select(TreatmentPhase).where(
        TreatmentPhase.treatment_plan_id == plan_id
    ).order_by(TreatmentPhase.phase_number)
    
    result = await db.execute(query)
    phases = result.scalars().all()
    
    return TreatmentPhaseListResponse(
        phases=phases,
        count=len(phases),
    )
@router.post("/plans/{plan_id}/phases", response_model=TreatmentPhaseResponse)
async def create_treatment_phase(
    plan_id: str,
    phase_data: TreatmentPhaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new treatment phase
    """
    # Verify plan belongs to practice
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment plan not found",
        )
    
    phase = TreatmentPhase(
        treatment_plan_id=plan_id,
        **phase_data.dict()
    )
    
    db.add(phase)
    await db.commit()
    await db.refresh(phase)
    
    return phase


@router.put("/phases/{phase_id}", response_model=TreatmentPhaseResponse)
async def update_treatment_phase(
    phase_id: str,
    phase_data: TreatmentPhaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update treatment phase
    """
    result = await db.execute(
        select(TreatmentPhase).where(TreatmentPhase.id == phase_id)
    )
    phase = result.scalar_one_or_none()
    
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment phase not found",
        )
    
    # Verify plan belongs to practice
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == phase.treatment_plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    update_data = phase_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(phase, field, value)
    
    await db.commit()
    await db.refresh(phase)
    
    return phase


# Treatment Procedure Endpoints

@router.get("/plans/{plan_id}/procedures", response_model=TreatmentProcedureListResponse)
async def list_treatment_procedures(
    plan_id: str,
    phase_id: Optional[str] = Query(None, description="Filter by phase"),
    status: Optional[str] = Query(None, description="Filter by status"),
    procedure_type: Optional[ProcedureType] = Query(None, description="Filter by type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List procedures for a treatment plan
    """
    # Verify plan belongs to practice
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment plan not found",
        )
    
    query = select(TreatmentProcedure).where(
        TreatmentProcedure.treatment_plan_id == plan_id
    )
    
    if phase_id:
        query = query.where(TreatmentProcedure.phase_id == phase_id)
    
    if status:
        query = query.where(TreatmentProcedure.status == status)
    
    if procedure_type:
        query = query.where(TreatmentProcedure.procedure_type == procedure_type)
    
    query = query.order_by(TreatmentProcedure.display_order)
    
    result = await db.execute(query)
    procedures = result.scalars().all()
    
    return TreatmentProcedureListResponse(
        procedures=procedures,
        count=len(procedures),
    )


@router.post("/plans/{plan_id}/procedures", response_model=TreatmentProcedureResponse)
async def create_treatment_procedure(
    plan_id: str,
    procedure_data: TreatmentProcedureCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new treatment procedure
    """
    # Verify plan belongs to practice
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment plan not found",
        )
    
    # Verify phase belongs to plan if provided
    if procedure_data.phase_id:
        result = await db.execute(
            select(TreatmentPhase).where(
                TreatmentPhase.id == procedure_data.phase_id,
                TreatmentPhase.treatment_plan_id == plan_id,
            )
        )
        phase = result.scalar_one_or_none()
        
        if not phase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Treatment phase not found",
            )
    
    procedure = TreatmentProcedure(
        treatment_plan_id=plan_id,
        **procedure_data.dict()
    )
    
    db.add(procedure)
    await db.commit()
    await db.refresh(procedure)
    
    # Update plan totals
    await update_plan_totals(plan_id, db)
    
    return procedure
@router.put("/procedures/{procedure_id}", response_model=TreatmentProcedureResponse)
async def update_treatment_procedure(
    procedure_id: str,
    procedure_data: TreatmentProcedureUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update treatment procedure
    """
    result = await db.execute(
        select(TreatmentProcedure).where(TreatmentProcedure.id == procedure_id)
    )
    procedure = result.scalar_one_or_none()
    
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment procedure not found",
        )
    
    # Verify plan belongs to practice
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == procedure.treatment_plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    update_data = procedure_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(procedure, field, value)
    
    await db.commit()
    await db.refresh(procedure)
    
    # Update plan totals
    await update_plan_totals(procedure.treatment_plan_id, db)
    
    return procedure


@router.delete("/procedures/{procedure_id}")
async def delete_treatment_procedure(
    procedure_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete treatment procedure
    """
    result = await db.execute(
        select(TreatmentProcedure).where(TreatmentProcedure.id == procedure_id)
    )
    procedure = result.scalar_one_or_none()
    
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment procedure not found",
        )
    
    # Verify plan belongs to practice
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == procedure.treatment_plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    plan_id = procedure.treatment_plan_id
    
    await db.delete(procedure)
    await db.commit()
    
    # Update plan totals
    await update_plan_totals(plan_id, db)
    
    return {"message": "Treatment procedure deleted successfully"}


# Procedure Library Endpoints

@router.get("/library/", response_model=ProcedureLibraryListResponse)
async def list_procedure_library(
    search: Optional[str] = Query(None, description="Search by code or description"),
    procedure_type: Optional[ProcedureType] = Query(None, description="Filter by type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List procedure library entries
    """
    query = select(ProcedureLibrary).where(
        ProcedureLibrary.practice_id == current_user.practice_id,
        ProcedureLibrary.is_archived == False,
    )
    
    if is_active is not None:
        query = query.where(ProcedureLibrary.is_active == is_active)
    
    if search:
        # Use parameterized query to prevent SQL injection
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                ProcedureLibrary.ada_code.ilike(search_pattern),
                ProcedureLibrary.description.ilike(search_pattern),
            )
        )
    
    if procedure_type:
        query = query.where(ProcedureLibrary.procedure_type == procedure_type)
    
    if category:
        query = query.where(ProcedureLibrary.category == category)
    
    query = query.order_by(ProcedureLibrary.ada_code)
    
    result = await db.execute(query)
    procedures = result.scalars().all()
    
    return ProcedureLibraryListResponse(
        procedures=procedures,
        count=len(procedures),
    )
@router.post("/library/", response_model=ProcedureLibraryResponse)
async def create_procedure_library_entry(
    procedure_data: ProcedureLibraryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new procedure library entry
    """
    # Check for duplicate ADA code
    result = await db.execute(
        select(ProcedureLibrary).where(
            ProcedureLibrary.ada_code == procedure_data.ada_code,
            ProcedureLibrary.practice_id == current_user.practice_id,
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Procedure with this ADA code already exists",
        )
    
    procedure = ProcedureLibrary(
        practice_id=current_user.practice_id,
        **procedure_data.dict()
    )
    
    db.add(procedure)
    await db.commit()
    await db.refresh(procedure)
    
    return procedure


@router.put("/library/{procedure_id}", response_model=ProcedureLibraryResponse)
async def update_procedure_library_entry(
    procedure_id: str,
    procedure_data: ProcedureLibraryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update procedure library entry
    """
    result = await db.execute(
        select(ProcedureLibrary).where(
            ProcedureLibrary.id == procedure_id,
            ProcedureLibrary.practice_id == current_user.practice_id,
        )
    )
    procedure = result.scalar_one_or_none()
    
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure library entry not found",
        )
    
    update_data = procedure_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(procedure, field, value)
    
    await db.commit()
    await db.refresh(procedure)
    
    return procedure


# Cost Estimation Endpoint

@router.post("/estimate", response_model=CostEstimateResponse)
async def estimate_costs(
    estimate_request: CostEstimateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Estimate costs for treatment procedures
    """
    total_fee = 0
    total_insurance_estimate = 0
    total_patient_responsibility = 0
    procedure_estimates = []
    
    # Get insurance information if provided
    insurance_details = None
    if estimate_request.patient_insurance_id:
        result = await db.execute(
            select(PatientInsurance).where(
                PatientInsurance.id == estimate_request.patient_insurance_id
            )
        )
        patient_insurance = result.scalar_one_or_none()
        
        if patient_insurance:
            # Verify patient belongs to practice
            result = await db.execute(
                select(Patient).where(
                    Patient.id == patient_insurance.patient_id,
                    Patient.practice_id == current_user.practice_id,
                )
            )
            patient = result.scalar_one_or_none()
            
            if patient:
                insurance_details = {
                    "carrier_name": patient_insurance.carrier.name if patient_insurance.carrier else None,
                    "coverage_percentages": {
                        "preventive": patient_insurance.preventive_coverage or 100,
                        "basic": patient_insurance.basic_coverage or 80,
                        "major": patient_insurance.major_coverage or 50,
                    },
                    "annual_maximum": float(patient_insurance.annual_maximum or 0),
                    "deductible_met": float(patient_insurance.deductible_met or 0),
                    "annual_deductible": float(patient_insurance.annual_deductible or 0),
                }
    
    # Calculate estimates for each procedure
    for proc_data in estimate_request.procedures:
        procedure_fee = proc_data.fee
        
        # Calculate insurance coverage if insurance details available
        insurance_coverage = 0
        if insurance_details:
            # Determine coverage percentage based on procedure type
            if proc_data.procedure_type == ProcedureType.PREVENTIVE:
                coverage_pct = insurance_details["coverage_percentages"]["preventive"]
            elif proc_data.procedure_type in [ProcedureType.RESTORATIVE, ProcedureType.ENDODONTIC]:
                coverage_pct = insurance_details["coverage_percentages"]["basic"]
            elif proc_data.procedure_type in [ProcedureType.PROSTHODONTIC, ProcedureType.ORAL_SURGERY, ProcedureType.ORTHODONTIC]:
                coverage_pct = insurance_details["coverage_percentages"]["major"]
            else:
                coverage_pct = 0
            
            insurance_coverage = procedure_fee * (coverage_pct / 100)
        
        patient_responsibility = procedure_fee - insurance_coverage
        
        total_fee += procedure_fee
        total_insurance_estimate += insurance_coverage
        total_patient_responsibility += patient_responsibility
        
        procedure_estimates.append({
            "ada_code": proc_data.ada_code,
            "description": proc_data.description,
            "fee": procedure_fee,
            "insurance_coverage": insurance_coverage,
            "patient_responsibility": patient_responsibility,
            "coverage_percentage": insurance_coverage / procedure_fee * 100 if procedure_fee > 0 else 0,
        })
    
    return CostEstimateResponse(
        total_fee=total_fee,
        total_insurance_estimate=total_insurance_estimate,
        total_patient_responsibility=total_patient_responsibility,
        procedure_estimates=procedure_estimates,
        insurance_details=insurance_details,
    )


# Plan Acceptance Endpoint

@router.post("/plans/{plan_id}/accept", response_model=PlanAcceptanceResponse)
async def accept_treatment_plan(
    plan_id: str,
    acceptance_data: PlanAcceptanceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Accept a treatment plan
    """
    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.id == plan_id,
            TreatmentPlan.practice_id == current_user.practice_id,
        )
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment plan not found",
        )
    
    # Update plan status
    plan.status = TreatmentPlanStatus.ACCEPTED
    plan.accepted_date = datetime.now().date()
    plan.acceptance_method = acceptance_data.acceptance_method
    plan.acceptance_notes = acceptance_data.acceptance_notes
    
    # Update accepted procedures if specified
    accepted_procedures = []
    total_accepted_cost = 0
    
    if acceptance_data.accepted_procedures:
        # Get all procedures for this plan
        result = await db.execute(
            select(TreatmentProcedure).where(
                TreatmentProcedure.treatment_plan_id == plan_id
            )
        )
        all_procedures = result.scalars().all()
        
        for procedure in all_procedures:
            if procedure.id in acceptance_data.accepted_procedures:
                procedure.is_accepted = True
                procedure.acceptance_notes = acceptance_data.acceptance_notes
                accepted_procedures.append(procedure.id)
                total_accepted_cost += procedure.fee
            else:
                procedure.is_accepted = False
    else:
        # Accept all procedures
        result = await db.execute(
            select(TreatmentProcedure).where(
                TreatmentProcedure.treatment_plan_id == plan_id
            )
        )
        all_procedures = result.scalars().all()
        
        for procedure in all_procedures:
            procedure.is_accepted = True
            procedure.acceptance_notes = acceptance_data.acceptance_notes
            accepted_procedures.append(procedure.id)
            total_accepted_cost += procedure.fee
    
    await db.commit()
    
    return PlanAcceptanceResponse(
        plan_id=plan.id,
        status=plan.status,
        accepted_date=plan.accepted_date,
        acceptance_method=plan.acceptance_method,
        total_accepted_cost=total_accepted_cost,
        accepted_procedures=accepted_procedures,
    )


# Helper Functions

async def update_plan_totals(plan_id: str, db: AsyncSession) -> None:
    """
    Update treatment plan totals based on procedures
    """
    # Get all procedures for this plan
    result = await db.execute(
        select(TreatmentProcedure).where(
            TreatmentProcedure.treatment_plan_id == plan_id
        )
    )
    procedures = result.scalars().all()
    
    # Calculate totals
    total_fee = sum(float(proc.fee or 0) for proc in procedures)
    total_insurance_estimate = sum(float(proc.insurance_estimate or 0) for proc in procedures)
    total_patient_responsibility = sum(float(proc.patient_responsibility or 0) for proc in procedures)
    
    # Update plan
    result = await db.execute(
        select(TreatmentPlan).where(TreatmentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if plan:
        plan.total_estimated_cost = total_fee
        plan.total_insurance_estimate = total_insurance_estimate
        plan.total_patient_responsibility = total_patient_responsibility
        
        await db.commit()