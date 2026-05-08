"""
Visual Dental Charting Service
Handles logic for tooth conditions, charting history, and linking with treatment plans.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.models.clinical import (
    DentalChart, ToothCondition, ChartingEntry, ChartingSymbol,
    ConditionType, RestorationStatus, SurfaceCode
)
from app.models.user import User
import json


class ChartingService:
    """Business logic for dental charting"""

    @staticmethod
    async def get_patient_chart(db: AsyncSession, patient_id: UUID) -> Dict[str, Any]:
        """Get the full chart context including conditions and historical entries"""
        
        # 1. Get the base dental chart record
        result = await db.execute(
            select(DentalChart).where(DentalChart.patient_id == patient_id)
        )
        base_chart = result.scalar_one_or_none()
        
        if not base_chart:
            # Create if it doesn't exist
            base_chart = DentalChart(patient_id=patient_id, chart_data={})
            db.add(base_chart)
            await db.commit()
            await db.refresh(base_chart)
            
        # 2. Get all tooth conditions
        result = await db.execute(
            select(ToothCondition).where(ToothCondition.patient_id == patient_id)
        )
        conditions = result.scalars().all()
        
        # 3. Assemble response
        conditions_data = []
        for c in conditions:
            conditions_data.append({
                "id": str(c.id),
                "tooth_number": c.tooth_number,
                "surface": c.surface,
                "condition_type": c.condition_type.value,
                "status": c.status.value,
                "severity": c.severity,
                "material": c.material,
                "notes": c.notes,
                "noted_date": c.noted_date.isoformat() if c.noted_date else None,
                "provider_id": str(c.provider_id) if c.provider_id else None
            })
            
        return {
            "chart_id": str(base_chart.id),
            "base_data": base_chart.chart_data,
            "conditions": conditions_data
        }

    @staticmethod
    async def add_condition(
        db: AsyncSession, 
        patient_id: UUID, 
        provider_id: UUID, 
        condition_data: Dict[str, Any]
    ) -> ToothCondition:
        """Add a new tooth condition and log to history"""
        
        condition = ToothCondition(
            patient_id=patient_id,
            provider_id=provider_id,
            tooth_number=condition_data.get("tooth_number"),
            surface=condition_data.get("surface"),
            condition_type=ConditionType(condition_data.get("condition_type")),
            status=RestorationStatus(condition_data.get("status", "existing")),
            severity=condition_data.get("severity"),
            material=condition_data.get("material"),
            notes=condition_data.get("notes")
        )
        
        db.add(condition)
        
        # Log to history
        entry = ChartingEntry(
            patient_id=patient_id,
            provider_id=provider_id,
            tooth_number=condition.tooth_number,
            entry_type="condition",
            data={
                "action": "added",
                "condition_type": condition.condition_type.value,
                "surface": condition.surface,
                "status": condition.status.value
            }
        )
        db.add(entry)
        
        await db.commit()
        await db.refresh(condition)
        return condition

    @staticmethod
    async def get_chart_history(db: AsyncSession, patient_id: UUID) -> List[Dict[str, Any]]:
        """Get timeline of all charting changes"""
        result = await db.execute(
            select(ChartingEntry).where(
                ChartingEntry.patient_id == patient_id
            ).order_by(ChartingEntry.created_at.desc())
        )
        entries = result.scalars().all()
        
        history = []
        for e in entries:
            history.append({
                "id": str(e.id),
                "patient_id": str(e.patient_id),
                "tooth_number": e.tooth_number,
                "entry_type": e.entry_type,
                "data": e.data,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "provider_id": str(e.provider_id) if e.provider_id else None
            })
        return history
