"""
Treatment Planning Endpoints
CRUD operations for treatment planning
Thin HTTP handlers that delegate to treatment services
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.api.deps import get_current_user, verify_csrf, require_role
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
from app.models.treatment import (
    TreatmentProcedure,
    ProcedureLibrary,
    TreatmentPlanStatus,
    ProcedureType,
)
from app.models.patient import Patient
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
    CostEstimateRequest,
    CostEstimateResponse,
    PlanAcceptanceRequest,
    PlanAcceptanceResponse,
)

# Import services
from app.services.treatment_service import TreatmentService
from app.services.treatment_planning import TreatmentPlanningService
from app.services.treatment_costing import TreatmentCostingService

router = APIRouter()
logger = logging.getLogger(__name__)


# Treatment Plan Endpoints

@router.get("/plans/", response_model=TreatmentPlanListResponse)
async def list_treatment_plans(
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    status_filter: Optional[TreatmentPlanStatus] = Query(None, description="Filter by status"),
    provider_id: Optional[str] = Query(None, description="Filter by provider"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TreatmentPlanListResponse:
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

        logger.info(f"Listed {len(plans)} treatment plans")
        return TreatmentPlanListResponse(plans=plans, count=len(plans))
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error listing treatment plans: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/patients/{patient_id}/plans", response_model=TreatmentPlanListResponse)
async def list_patient_treatment_plans(
    patient_id: str,
    status_filter: Optional[TreatmentPlanStatus] = Query(None, description="Filter by status"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TreatmentPlanListResponse:
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
    except ValueError as e:
        logger.error(f"Validation error listing patient treatment plans: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request parameters")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Unexpected error listing patient treatment plans: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/plans/", response_model=TreatmentPlanResponse)
async def create_treatment_plan(
    plan_data: TreatmentPlanCreate,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> TreatmentPlanResponse:
    """Create a new treatment plan"""
    try:
        # Verify patient belongs to practice
        result = await db.execute(
            select(Patient).where(
                Patient.id == plan_data.patient_id,
                Patient.practice_id == current_user.practice_id,
            )
        )
        patient = result.scalar_one_or_none()

        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

        # Verify provider belongs to practice
        result = await db.execute(
            select(User).where(
                User.id == plan_data.provider_id,
                User.practice_id == current_user.practice_id,
            )
        )
        provider = result.scalar_one_or_none()

        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

        plan = await TreatmentService.create_treatment_plan(
            db,
            current_user.practice_id,
            plan_data.patient_id,
            plan_data.provider_id,
            **plan_data.dict(exclude={"patient_id", "provider_id"})
        )

        # HIPAA: Log creation
        await log_audit_event(db, current_user, "create_treatment_plan", "treatment_plan", plan.id, request)
        await db.commit()

        logger.info(f"Created treatment plan: {plan.id}")
        return plan
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error creating treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid treatment plan data")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Unexpected error creating treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/plans/{plan_id}", response_model=TreatmentPlanResponse)
async def get_treatment_plan(
    plan_id: UUID,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TreatmentPlanResponse:
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
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Unexpected error getting treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/plans/{plan_id}", response_model=TreatmentPlanResponse)
async def update_treatment_plan(
    plan_id: UUID,
    plan_data: TreatmentPlanUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> TreatmentPlanResponse:
    """Update treatment plan"""
    try:
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)

        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")

        plan = await TreatmentService.update_treatment_plan(
            db,
            plan_id,
            **plan_data.model_dump(exclude_unset=True)
        )

        logger.info(f"Updated treatment plan: {plan_id}")
        return plan
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error updating treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/plans/{plan_id}")
async def delete_treatment_plan(
    plan_id: UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> dict:
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
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error deleting treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Treatment Phase Endpoints

@router.get("/plans/{plan_id}/phases", response_model=TreatmentPhaseListResponse)
async def list_treatment_phases(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TreatmentPhaseListResponse:
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
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error listing treatment phases: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/plans/{plan_id}/phases", response_model=TreatmentPhaseResponse)
async def create_treatment_phase(
    plan_id: UUID,
    phase_data: TreatmentPhaseCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> TreatmentPhaseResponse:
    """Create a new treatment phase"""
    try:
        # Verify plan belongs to practice
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)

        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")

        phase = await TreatmentPlanningService.create_treatment_phase(
            db,
            plan_id,
            **phase_data.model_dump()
        )

        logger.info(f"Created treatment phase: {phase.id}")
        return phase
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error creating treatment phase: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/phases/{phase_id}", response_model=TreatmentPhaseResponse)
async def update_treatment_phase(
    phase_id: UUID,
    phase_data: TreatmentPhaseUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> TreatmentPhaseResponse:
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
            **phase_data.model_dump(exclude_unset=True)
        )

        logger.info(f"Updated treatment phase: {phase_id}")
        return phase
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error updating treatment phase: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Treatment Procedure Endpoints

@router.get("/plans/{plan_id}/procedures", response_model=TreatmentProcedureListResponse)
async def list_treatment_procedures(
    plan_id: UUID,
    phase_id: Optional[UUID] = Query(None, description="Filter by phase"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    procedure_type: Optional[ProcedureType] = Query(None, description="Filter by type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TreatmentProcedureListResponse:
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
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error listing treatment procedures: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/plans/{plan_id}/procedures", response_model=TreatmentProcedureResponse)
async def create_treatment_procedure(
    plan_id: str,
    procedure_data: TreatmentProcedureCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> TreatmentProcedureResponse:
    """Create a new treatment procedure"""
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

        procedure = TreatmentProcedure(
            treatment_plan_id=plan_id,
            **procedure_data.dict()
        )

        db.add(procedure)
        await db.commit()
        await db.refresh(procedure)

        # Update plan totals
        await TreatmentCostingService.update_plan_totals(db, plan_id)

        logger.info(f"Created treatment procedure: {procedure.id}")
        return procedure
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error creating treatment procedure: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/procedures/{procedure_id}", response_model=TreatmentProcedureResponse)
async def update_treatment_procedure(
    procedure_id: str,
    procedure_data: TreatmentProcedureUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> TreatmentProcedureResponse:
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
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error updating treatment procedure: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/procedures/{procedure_id}")
async def delete_treatment_procedure(
    procedure_id: str,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> dict:
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
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
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
) -> ProcedureLibraryListResponse:
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
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error listing procedure library: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/library/", response_model=ProcedureLibraryResponse)
async def create_procedure_library_entry(
    procedure_data: ProcedureLibraryCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> ProcedureLibraryResponse:
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
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error creating procedure library entry: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/library/{procedure_id}", response_model=ProcedureLibraryResponse)
async def update_procedure_library_entry(
    procedure_id: str,
    procedure_data: ProcedureLibraryUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> ProcedureLibraryResponse:
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
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error updating procedure library entry: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Cost Estimation Endpoint

@router.post("/estimate", response_model=CostEstimateResponse)
async def estimate_costs(
    estimate_request: CostEstimateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CostEstimateResponse:
    """Estimate costs for treatment procedures"""
    try:
        result = await TreatmentCostingService.estimate_insurance_coverage(
            db,
            estimate_request.patient_insurance_id,
            estimate_request.procedures,
        )

        logger.info(f"Generated cost estimate for {len(estimate_request.procedures)} procedures")
        return CostEstimateResponse(**result)
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error estimating costs: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# Plan Acceptance Endpoint

@router.post("/plans/{plan_id}/accept", response_model=PlanAcceptanceResponse)
async def accept_treatment_plan(
    plan_id: str,
    acceptance_data: PlanAcceptanceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> PlanAcceptanceResponse:
    """Accept a treatment plan"""
    try:
        plan = await TreatmentService.get_treatment_plan(db, plan_id, current_user.practice_id)

        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Treatment plan not found")

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
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource already exists")
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Error accepting treatment plan: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")