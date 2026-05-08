"""
Treatment Planning Endpoints
CRUD operations for treatment planning
Thin HTTP handlers that delegate to treatment services
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, and_, or_
from datetime import datetime, date, timezone
from typing import List, Optional, Any
import logging
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, verify_csrf, require_role
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
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
from app.models.insurance import PatientInsurance
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

# Import services
from app.services.treatment_service import TreatmentService
from app.services.treatment_planning import TreatmentPlanningService
from app.services.treatment_costing import TreatmentCostingService

router = APIRouter()
logger = logging.getLogger(__name__)


# Treatment Plan Endpoints

@router.get("/plans", response_model=TreatmentPlanListResponse)
async def list_treatment_plans(
    patient_id: Optional[uuid.UUID] = Query(None, description="Filter by patient"),
    status_filter: Optional[TreatmentPlanStatus] = Query(None, description="Filter by status"),
    provider_id: Optional[uuid.UUID] = Query(None, description="Filter by provider"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List treatment plans for the current practice"""
    try:
        plans = await TreatmentService.list_treatment_plans(
            db,
            current_user.practice_id,
            patient_id=patient_id,
            status=status_filter,
            provider_id=provider_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        # HIPAA: Log access
        await log_audit_event(db, current_user, "list_treatment_plans", "treatment_plan", None, request)
        await db.commit()
        
        return TreatmentPlanListResponse(plans=plans, count=len(plans))
    except Exception as e:
        logger.error(f"Error listing treatment plans: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/plans", response_model=TreatmentPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_treatment_plan(
    plan_data: TreatmentPlanCreate,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new treatment plan
    CRIT-19 FIX: Explicit field mapping to prevent Cross-Tenant ID injection
    """
    try:
        # 1. Verify patient belongs to practice
        result = await db.execute(
            select(Patient).where(
                Patient.id == plan_data.patient_id,
                Patient.practice_id == current_user.practice_id,
            )
        )
        patient = result.scalar_one_or_none()
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        # 2. Verify provider belongs to practice (if provided)
        if plan_data.provider_id:
            result = await db.execute(
                select(User).where(
                    User.id == plan_data.provider_id,
                    User.practice_id == current_user.practice_id,
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

        # 3. Create plan with explicit field assignment
        plan = TreatmentPlan(
            practice_id=current_user.practice_id,
            patient_id=plan_data.patient_id,
            provider_id=plan_data.provider_id or current_user.id,
            plan_name=plan_data.plan_name,
            status=plan_data.status,
            chief_complaint=plan_data.chief_complaint,
            diagnosis=plan_data.diagnosis,
            treatment_goals=plan_data.treatment_goals,
            target_start_date=plan_data.target_start_date or plan_data.start_date,
            target_completion_date=plan_data.target_completion_date or plan_data.estimated_completion_date,
            notes=plan_data.notes or plan_data.description,
            visual_config=plan_data.visual_config,
            total_estimated_cost=plan_data.estimated_cost or plan_data.total_cost or 0,
            total_insurance_estimate=plan_data.insurance_coverage or 0,
        )
        db.add(plan)
        await db.flush()
        
        # HIPAA: Log creation
        await log_audit_event(db, current_user, "create_treatment_plan", "treatment_plan", plan.id, request)
        await db.commit()
        await db.refresh(plan)
        
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.patch("/plans/{plan_id}", response_model=TreatmentPlanResponse)
async def patch_treatment_plan(
    plan_id: uuid.UUID,
    plan_data: TreatmentPlanUpdate,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Partially update a treatment plan
    B-15 FIX: Added HIPAA audit logging
    """
    try:
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")

        update_data = plan_data.model_dump(exclude_unset=True)
        # Prevent ID/Practice manipulation
        update_data.pop('id', None)
        update_data.pop('practice_id', None)
        update_data.pop('patient_id', None)

        for field, value in update_data.items():
            if hasattr(plan, field):
                setattr(plan, field, value)

        # HIPAA: Log modification
        await log_audit_event(db, current_user, "update_treatment_plan", "treatment_plan", plan.id, request, {"patch": True})
        await db.commit()
        await db.refresh(plan)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/patients/{patient_id}/plans", response_model=TreatmentPlanListResponse)
async def list_patient_treatment_plans(
    patient_id: uuid.UUID,
    status_filter: Optional[TreatmentPlanStatus] = Query(None, description="Filter by status"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List treatment plans for a specific patient"""
    try:
        # Verify patient belongs to practice
        result = await db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.practice_id == current_user.practice_id,
            )
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        
        plans = await TreatmentService.list_treatment_plans(
            db,
            current_user.practice_id,
            patient_id=patient_id,
            status=status_filter,
        )
        
        # HIPAA: Log access
        await log_audit_event(db, current_user, "list_patient_treatment_plans", "patient", patient_id, request)
        await db.commit()
        
        logger.info(f"Listed {len(plans)} treatment plans for patient: {patient_id}")
        return TreatmentPlanListResponse(plans=plans, count=len(plans))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing patient treatment plans: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/plans/{plan_id}", response_model=TreatmentPlanResponse)
async def get_treatment_plan(
    plan_id: uuid.UUID,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get treatment plan by ID"""
    try:
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")
        
        # HIPAA: Log access
        await log_audit_event(db, current_user, "view_treatment_plan", "treatment_plan", plan.id, request)
        await db.commit()
        
        logger.info(f"Retrieved treatment plan: {plan_id}")
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/plans/{plan_id}", response_model=TreatmentPlanResponse)
async def update_treatment_plan(
    plan_id: uuid.UUID,
    plan_data: TreatmentPlanUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Update treatment plan"""
    try:
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")
        
        plan = await TreatmentService.update_treatment_plan(
            db,
            plan_id,
            **plan_data.dict(exclude_unset=True)
        )
        
        logger.info(f"Updated treatment plan: {plan_id}")
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/plans/{plan_id}")
async def delete_treatment_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Delete treatment plan (soft delete via status change)"""
    try:
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")
        
        success = await TreatmentService.delete_treatment_plan(db, plan_id)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete plan")
        
        logger.info(f"Deleted treatment plan: {plan_id}")
        return {"message": "Treatment plan cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Treatment Phase Endpoints

@router.get("/plans/{plan_id}/phases", response_model=TreatmentPhaseListResponse)
async def list_treatment_phases(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List phases for a treatment plan"""
    try:
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")
        
        phases = await TreatmentPlanningService.list_treatment_phases(db, plan_id)
        
        logger.info(f"Listed {len(phases)} treatment phases")
        return TreatmentPhaseListResponse(phases=phases, count=len(phases))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing treatment phases: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/plans/{plan_id}/phases", response_model=TreatmentPhaseResponse)
async def create_treatment_phase(
    plan_id: uuid.UUID,
    phase_data: TreatmentPhaseCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Create a new treatment phase"""
    try:
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")
        
        phase = await TreatmentPlanningService.create_treatment_phase(
            db,
            plan_id,
            **phase_data.dict()
        )
        
        logger.info(f"Created treatment phase: {phase.id}")
        return phase
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating treatment phase: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/phases/{phase_id}", response_model=TreatmentPhaseResponse)
async def update_treatment_phase(
    phase_id: uuid.UUID,
    phase_data: TreatmentPhaseUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Update treatment phase"""
    try:
        phase = await TreatmentPlanningService.get_treatment_phase(db, phase_id)
        
        if not phase:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment phase not found")
        
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, phase.treatment_plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        phase = await TreatmentPlanningService.update_treatment_phase(
            db,
            phase_id,
            **phase_data.dict(exclude_unset=True)
        )
        
        logger.info(f"Updated treatment phase: {phase_id}")
        return phase
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating treatment phase: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Treatment Procedure Endpoints

@router.get("/plans/{plan_id}/procedures", response_model=TreatmentProcedureListResponse)
async def list_treatment_procedures(
    plan_id: uuid.UUID,
    phase_id: Optional[uuid.UUID] = Query(None, description="Filter by phase"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    procedure_type: Optional[ProcedureType] = Query(None, description="Filter by type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List procedures for a treatment plan"""
    try:
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")
        
        query = select(TreatmentProcedure).where(
            TreatmentProcedure.treatment_plan_id == plan_id
        )
        
        if phase_id:
            query = query.where(TreatmentProcedure.phase_id == phase_id)
        
        if status_filter:
            query = query.where(TreatmentProcedure.status == status_filter)
        
        if procedure_type:
            query = query.where(TreatmentProcedure.procedure_type == procedure_type)
        
        query = query.order_by(TreatmentProcedure.display_order)
        
        result = await db.execute(query)
        procedures = result.scalars().all()
        
        logger.info(f"Listed {len(procedures)} treatment procedures")
        return TreatmentProcedureListResponse(procedures=procedures, count=len(procedures))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing treatment procedures: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/plans/{plan_id}/procedures", response_model=TreatmentProcedureResponse)
async def create_treatment_procedure(
    plan_id: uuid.UUID,
    procedure_data: TreatmentProcedureCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new treatment procedure
    CRIT-19 FIX: Explicit field mapping to prevent injection
    """
    try:
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")
        
        # Verify phase belongs to plan if provided
        if procedure_data.phase_id:
            phase = await TreatmentPlanningService.get_treatment_phase(db, procedure_data.phase_id)
            if not phase or phase.treatment_plan_id != plan_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment phase not found")
        
        # Explicit mapping (Prevent ID injection)
        procedure = TreatmentProcedure(
            treatment_plan_id=plan_id,
            ada_code=procedure_data.ada_code,
            description=procedure_data.description,
            tooth_number=procedure_data.tooth_number,
            surface=procedure_data.surface,
            fee=procedure_data.fee,
            status=procedure_data.status,
            phase_id=procedure_data.phase_id,
            procedure_type=procedure_data.procedure_type,
            notes=procedure_data.notes,
            display_order=procedure_data.display_order,
            is_completed=procedure_data.is_completed,
            completion_date=procedure_data.completion_date,
            provider_id=procedure_data.provider_id or plan.provider_id,
        )
        
        db.add(procedure)
        await db.commit()
        await db.refresh(procedure)
        
        # Update plan totals
        await TreatmentCostingService.update_plan_totals(db, plan_id)
        
        return procedure
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating treatment procedure: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/procedures/{procedure_id}", response_model=TreatmentProcedureResponse)
async def update_treatment_procedure(
    procedure_id: uuid.UUID,
    procedure_data: TreatmentProcedureUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Update treatment procedure"""
    try:
        result = await db.execute(
            select(TreatmentProcedure).where(TreatmentProcedure.id == procedure_id)
        )
        procedure = result.scalar_one_or_none()
        
        if not procedure:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment procedure not found")
        
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, procedure.treatment_plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        update_data = procedure_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(procedure, field, value)
        
        await db.commit()
        await db.refresh(procedure)
        
        # Update plan totals
        await TreatmentCostingService.update_plan_totals(db, procedure.treatment_plan_id)
        
        logger.info(f"Updated treatment procedure: {procedure_id}")
        return procedure
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating treatment procedure: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/procedures/{procedure_id}")
async def delete_treatment_procedure(
    procedure_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Delete treatment procedure"""
    try:
        result = await db.execute(
            select(TreatmentProcedure).where(TreatmentProcedure.id == procedure_id)
        )
        procedure = result.scalar_one_or_none()
        
        if not procedure:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment procedure not found")
        
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, procedure.treatment_plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        plan_id = procedure.treatment_plan_id
        
        await db.delete(procedure)
        await db.commit()
        
        # Update plan totals
        await TreatmentCostingService.update_plan_totals(db, plan_id)
        
        logger.info(f"Deleted treatment procedure: {procedure_id}")
        return {"message": "Treatment procedure deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting treatment procedure: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


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
    """List procedure library entries"""
    try:
        query = select(ProcedureLibrary).where(
            ProcedureLibrary.practice_id == current_user.practice_id,
            ProcedureLibrary.is_archived == False,
        )
        
        if is_active is not None:
            query = query.where(ProcedureLibrary.is_active == is_active)
        
        if search:
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
        
        logger.info(f"Listed {len(procedures)} procedure library entries")
        return ProcedureLibraryListResponse(procedures=procedures, count=len(procedures))
    except Exception as e:
        logger.error(f"Error listing procedure library: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/library/", response_model=ProcedureLibraryResponse)
async def create_procedure_library_entry(
    procedure_data: ProcedureLibraryCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Create a new procedure library entry"""
    try:
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
        
        logger.info(f"Created procedure library entry: {procedure.id}")
        return procedure
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating procedure library entry: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/library/{procedure_id}", response_model=ProcedureLibraryResponse)
async def update_procedure_library_entry(
    procedure_id: uuid.UUID,
    procedure_data: ProcedureLibraryUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Update procedure library entry"""
    try:
        result = await db.execute(
            select(ProcedureLibrary).where(
                ProcedureLibrary.id == procedure_id,
                ProcedureLibrary.practice_id == current_user.practice_id,
            )
        )
        procedure = result.scalar_one_or_none()
        
        if not procedure:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procedure library entry not found")
        
        update_data = procedure_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(procedure, field, value)
        
        await db.commit()
        await db.refresh(procedure)
        
        logger.info(f"Updated procedure library entry: {procedure_id}")
        return procedure
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating procedure library entry: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Cost Estimation Endpoint

@router.post("/estimate", response_model=CostEstimateResponse)
async def estimate_costs(
    estimate_request: CostEstimateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Estimate costs for treatment procedures
    CRIT-20 FIX: Ownership verification for Insurance ID
    """
    try:
        # Verify insurance belongs to practice (CRIT-20)
        result = await db.execute(
            select(PatientInsurance).join(Patient).where(
                PatientInsurance.id == estimate_request.patient_insurance_id,
                Patient.practice_id == current_user.practice_id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance record not found")

        result = await TreatmentCostingService.estimate_insurance_coverage(
            db,
            estimate_request.patient_insurance_id,
            estimate_request.procedures,
        )
        
        return CostEstimateResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error estimating costs: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Plan Acceptance Endpoint

@router.post("/plans/{plan_id}/accept", response_model=PlanAcceptanceResponse)
async def accept_treatment_plan(
    plan_id: uuid.UUID,
    acceptance_data: PlanAcceptanceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Accept a treatment plan"""
    try:
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)
        
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")
        
        # Update plan status
        plan.status = TreatmentPlanStatus.ACCEPTED
        plan.accepted_date = datetime.now(timezone.utc).date()
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
                    total_accepted_cost += float(procedure.fee or 0)
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
                total_accepted_cost += float(procedure.fee or 0)
        
        await db.commit()
        
        logger.info(f"Accepted treatment plan: {plan_id}")
        return PlanAcceptanceResponse(
            plan_id=plan.id,
            status=plan.status,
            accepted_date=plan.accepted_date,
            acceptance_method=plan.acceptance_method,
            total_accepted_cost=total_accepted_cost,
            accepted_procedures=accepted_procedures,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")