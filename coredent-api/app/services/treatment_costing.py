"""
Treatment Costing Service
Cost calculations and insurance coverage estimation
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.treatment import (
    TreatmentPlan,
    TreatmentProcedure,
    ProcedureType,
)
from app.models.insurance import PatientInsurance

logger = logging.getLogger(__name__)


class TreatmentCostingService:
    """Service for treatment costing operations"""

    @staticmethod
    async def calculate_treatment_cost(
        db: AsyncSession,
        plan_id: UUID,
    ) -> Dict[str, float]:
        """Calculate total cost for a treatment plan"""
        result = await db.execute(
            select(TreatmentProcedure).where(
                TreatmentProcedure.treatment_plan_id == plan_id
            )
        )
        procedures = result.scalars().all()

        total_fee = sum(float(proc.fee or 0) for proc in procedures)
        total_insurance_estimate = sum(float(proc.insurance_estimate or 0) for proc in procedures)
        total_patient_responsibility = sum(float(proc.patient_responsibility or 0) for proc in procedures)

        return {
            "total_fee": total_fee,
            "total_insurance_estimate": total_insurance_estimate,
            "total_patient_responsibility": total_patient_responsibility,
        }

    @staticmethod
    async def estimate_insurance_coverage(
        db: AsyncSession,
        patient_insurance_id: UUID,
        procedures: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Estimate insurance coverage for procedures"""
        result = await db.execute(
            select(PatientInsurance).where(
                PatientInsurance.id == patient_insurance_id
            )
        )
        patient_insurance = result.scalar_one_or_none()

        if not patient_insurance:
            return {
                "total_fee": 0,
                "total_insurance_estimate": 0,
                "total_patient_responsibility": 0,
                "procedure_estimates": [],
            }

        total_fee = 0
        total_insurance_estimate = 0
        total_patient_responsibility = 0
        procedure_estimates = []

        # Coverage percentages
        coverage_percentages = {
            "preventive": patient_insurance.preventive_coverage or 100,
            "basic": patient_insurance.basic_coverage or 80,
            "major": patient_insurance.major_coverage or 50,
        }

        for proc_data in procedures:
            procedure_fee = proc_data.get("fee", 0)
            procedure_type = proc_data.get("procedure_type", ProcedureType.RESTORATIVE)

            # Determine coverage percentage
            if procedure_type == ProcedureType.PREVENTIVE:
                coverage_pct = coverage_percentages["preventive"]
            elif procedure_type in [ProcedureType.RESTORATIVE, ProcedureType.ENDODONTIC]:
                coverage_pct = coverage_percentages["basic"]
            elif procedure_type in [ProcedureType.PROSTHODONTIC, ProcedureType.ORAL_SURGERY, ProcedureType.ORTHODONTIC]:
                coverage_pct = coverage_percentages["major"]
            else:
                coverage_pct = 0

            insurance_coverage = procedure_fee * (coverage_pct / 100)
            patient_responsibility = procedure_fee - insurance_coverage

            total_fee += procedure_fee
            total_insurance_estimate += insurance_coverage
            total_patient_responsibility += patient_responsibility

            procedure_estimates.append({
                "ada_code": proc_data.get("ada_code"),
                "description": proc_data.get("description"),
                "fee": procedure_fee,
                "insurance_coverage": insurance_coverage,
                "patient_responsibility": patient_responsibility,
                "coverage_percentage": (insurance_coverage / procedure_fee * 100) if procedure_fee > 0 else 0,
            })

        return {
            "total_fee": total_fee,
            "total_insurance_estimate": total_insurance_estimate,
            "total_patient_responsibility": total_patient_responsibility,
            "procedure_estimates": procedure_estimates,
            "insurance_details": {
                "carrier_name": patient_insurance.carrier.name if patient_insurance.carrier else None,
                "coverage_percentages": coverage_percentages,
                "annual_maximum": float(patient_insurance.annual_maximum or 0),
                "deductible_met": float(patient_insurance.deductible_met or 0),
                "annual_deductible": float(patient_insurance.annual_deductible or 0),
            },
        }

    @staticmethod
    async def calculate_patient_responsibility(
        db: AsyncSession,
        plan_id: UUID,
        patient_insurance_id: Optional[UUID] = None,
    ) -> Dict[str, float]:
        """Calculate patient responsibility for a plan"""
        result = await db.execute(
            select(TreatmentProcedure).where(
                TreatmentProcedure.treatment_plan_id == plan_id
            )
        )
        procedures = result.scalars().all()

        if not procedures:
            return {
                "total_fee": 0,
                "insurance_coverage": 0,
                "patient_responsibility": 0,
            }

        total_fee = sum(float(proc.fee or 0) for proc in procedures)

        if patient_insurance_id:
            result = await db.execute(
                select(PatientInsurance).where(
                    PatientInsurance.id == patient_insurance_id
                )
            )
            patient_insurance = result.scalar_one_or_none()

            if patient_insurance:
                # Calculate insurance coverage
                insurance_coverage = 0
                for proc in procedures:
                    if proc.procedure_type == ProcedureType.PREVENTIVE:
                        coverage_pct = patient_insurance.preventive_coverage or 100
                    elif proc.procedure_type in [ProcedureType.RESTORATIVE, ProcedureType.ENDODONTIC]:
                        coverage_pct = patient_insurance.basic_coverage or 80
                    elif proc.procedure_type in [ProcedureType.PROSTHODONTIC, ProcedureType.ORAL_SURGERY, ProcedureType.ORTHODONTIC]:
                        coverage_pct = patient_insurance.major_coverage or 50
                    else:
                        coverage_pct = 0

                    insurance_coverage += float(proc.fee or 0) * (coverage_pct / 100)

                patient_responsibility = total_fee - insurance_coverage

                return {
                    "total_fee": total_fee,
                    "insurance_coverage": insurance_coverage,
                    "patient_responsibility": patient_responsibility,
                }

        # No insurance
        return {
            "total_fee": total_fee,
            "insurance_coverage": 0,
            "patient_responsibility": total_fee,
        }

    @staticmethod
    async def update_plan_totals(
        db: AsyncSession,
        plan_id: UUID,
    ) -> bool:
        """Update treatment plan totals based on procedures"""
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
        plan = await db.get(TreatmentPlan, plan_id)

        if not plan:
            return False

        plan.total_estimated_cost = total_fee
        plan.total_insurance_estimate = total_insurance_estimate
        plan.total_patient_responsibility = total_patient_responsibility

        await db.commit()
        logger.info(f"Updated plan totals: {plan_id}")
        return True

    @staticmethod
    async def get_cost_breakdown(
        db: AsyncSession,
        plan_id: UUID,
    ) -> Dict[str, Any]:
        """Get detailed cost breakdown for a plan"""
        result = await db.execute(
            select(TreatmentProcedure).where(
                TreatmentProcedure.treatment_plan_id == plan_id
            )
        )
        procedures = result.scalars().all()

        breakdown_by_type = {}

        for proc in procedures:
            proc_type = proc.procedure_type or "unknown"

            if proc_type not in breakdown_by_type:
                breakdown_by_type[proc_type] = {
                    "count": 0,
                    "total_fee": 0,
                    "total_insurance": 0,
                    "total_patient": 0,
                }

            breakdown_by_type[proc_type]["count"] += 1
            breakdown_by_type[proc_type]["total_fee"] += float(proc.fee or 0)
            breakdown_by_type[proc_type]["total_insurance"] += float(proc.insurance_estimate or 0)
            breakdown_by_type[proc_type]["total_patient"] += float(proc.patient_responsibility or 0)

        total_fee = sum(float(proc.fee or 0) for proc in procedures)
        total_insurance = sum(float(proc.insurance_estimate or 0) for proc in procedures)
        total_patient = sum(float(proc.patient_responsibility or 0) for proc in procedures)

        return {
            "total_fee": total_fee,
            "total_insurance": total_insurance,
            "total_patient": total_patient,
            "breakdown_by_type": breakdown_by_type,
            "procedure_count": len(procedures),
        }
