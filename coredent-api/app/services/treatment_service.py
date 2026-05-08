"""
Treatment Service
Core business logic for treatment operations
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.models.treatment import (
    TreatmentPlan,
    TreatmentPhase,
    TreatmentProcedure,
    TreatmentPlanStatus,
)
from app.models.patient import Patient
from app.models.user import User

logger = logging.getLogger(__name__)


class TreatmentService:
    """Service for treatment operations"""
    
    @staticmethod
    async def create_treatment_plan(
        db: AsyncSession,
        practice_id: UUID,
        patient_id: UUID,
        provider_id: UUID,
        **kwargs
    ) -> TreatmentPlan:
        """Create a new treatment plan"""
        plan = TreatmentPlan(
            practice_id=practice_id,
            patient_id=patient_id,
            provider_id=provider_id,
            **kwargs
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        logger.info(f"Created treatment plan: {plan.id}")
        return plan
    
    @staticmethod
    async def get_treatment_plan(
        db: AsyncSession,
        plan_id: UUID,
        practice_id: Optional[UUID] = None,
    ) -> Optional[TreatmentPlan]:
        """Get a treatment plan"""
        query = select(TreatmentPlan).where(TreatmentPlan.id == plan_id)
        
        if practice_id:
            query = query.where(TreatmentPlan.practice_id == practice_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_treatment_plan(
        db: AsyncSession,
        plan_id: UUID,
        **kwargs
    ) -> Optional[TreatmentPlan]:
        """Update a treatment plan"""
        result = await db.execute(
            select(TreatmentPlan).where(TreatmentPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return None
        
        # Handle status changes
        if 'status' in kwargs:
            new_status = kwargs['status']
            if new_status == TreatmentPlanStatus.PRESENTED and not plan.presented_date:
                plan.presented_date = datetime.now().date()
            elif new_status == TreatmentPlanStatus.ACCEPTED and not plan.accepted_date:
                plan.accepted_date = datetime.now().date()
        
        for key, value in kwargs.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
        
        await db.commit()
        await db.refresh(plan)
        logger.info(f"Updated treatment plan: {plan_id}")
        return plan
    
    @staticmethod
    async def list_treatment_plans(
        db: AsyncSession,
        practice_id: UUID,
        patient_id: Optional[UUID] = None,
        status: Optional[TreatmentPlanStatus] = None,
        provider_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[TreatmentPlan]:
        """List treatment plans with filtering"""
        query = (
            select(TreatmentPlan)
            .where(TreatmentPlan.practice_id == practice_id)
            .options(
                joinedload(TreatmentPlan.patient),
                joinedload(TreatmentPlan.provider)
            )
        )
        
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
        return result.scalars().all()
    
    @staticmethod
    async def delete_treatment_plan(
        db: AsyncSession,
        plan_id: UUID,
    ) -> bool:
        """Soft delete a treatment plan"""
        result = await db.execute(
            select(TreatmentPlan).where(TreatmentPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return False
        
        plan.status = TreatmentPlanStatus.CANCELLED
        await db.commit()
        logger.info(f"Deleted treatment plan: {plan_id}")
        return True
    
    @staticmethod
    async def get_plan_statistics(
        db: AsyncSession,
        plan_id: UUID,
    ) -> Dict[str, Any]:
        """Get statistics for a treatment plan"""
        plan = await TreatmentService.get_treatment_plan(db, plan_id)
        
        if not plan:
            return {}
        
        # Get procedures
        result = await db.execute(
            select(TreatmentProcedure).where(
                TreatmentProcedure.treatment_plan_id == plan_id
            )
        )
        procedures = result.scalars().all()
        
        total_procedures = len(procedures)
        accepted_procedures = sum(1 for p in procedures if p.is_accepted)
        completed_procedures = sum(1 for p in procedures if p.status == "completed")
        
        return {
            "total_procedures": total_procedures,
            "accepted_procedures": accepted_procedures,
            "completed_procedures": completed_procedures,
            "acceptance_rate": (accepted_procedures / total_procedures * 100) if total_procedures > 0 else 0,
            "completion_rate": (completed_procedures / total_procedures * 100) if total_procedures > 0 else 0,
            "total_estimated_cost": float(plan.total_estimated_cost or 0),
            "total_insurance_estimate": float(plan.total_insurance_estimate or 0),
            "total_patient_responsibility": float(plan.total_patient_responsibility or 0),
        }
