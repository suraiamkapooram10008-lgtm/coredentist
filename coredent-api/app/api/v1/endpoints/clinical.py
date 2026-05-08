"""
Clinical Endpoints
Operations for Perio Charting and clinical records
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Any, Dict, List
import uuid

from app.core.database import get_db
from app.models.user import User, UserRole
from app.api.deps import get_current_user, require_role, verify_csrf
from app.models.clinical import PerioChart, PerioChartEntry
from app.models.patient import Patient
from app.schemas.clinical import (
    PerioChartCreate,
    PerioChartResponse,
    PerioChartListResponse,
    ToothConditionCreate,
    ToothConditionResponse,
    ChartingEntryResponse,
    ChartingSymbolCreate,
    ChartingSymbolResponse,
    DentalChartResponse,
)
from app.services.charting_service import ChartingService
from app.models.clinical import ChartingSymbol, ToothCondition
from app.core.audit import log_audit_event

router = APIRouter()

# --- Visual Charting ---

@router.get("/chart/{patient_id}", response_model=DentalChartResponse)
async def get_patient_chart(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> Any:
    """Get the full visual chart context for a patient"""
    # Verify patient
    p_uuid = uuid.UUID(patient_id)
    result = await db.execute(
        select(Patient).where(Patient.id == p_uuid, Patient.practice_id == current_user.practice_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")
        
    chart_data = await ChartingService.get_patient_chart(db, p_uuid)
    
    await log_audit_event(db, current_user, "view_chart", "dental_chart", None, request, {"patient_id": patient_id})
    return chart_data


@router.post("/chart/{patient_id}/conditions", response_model=ToothConditionResponse)
async def add_tooth_condition(
    patient_id: str,
    condition_data: ToothConditionCreate,
    current_user: User = Depends(require_role(UserRole.DENTIST, UserRole.HYGIENIST, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Add a condition to a tooth"""
    # Verify patient
    p_uuid = uuid.UUID(patient_id)
    result = await db.execute(
        select(Patient).where(Patient.id == p_uuid, Patient.practice_id == current_user.practice_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Patient not found")
        
    condition = await ChartingService.add_condition(
        db, p_uuid, current_user.id, condition_data.dict(exclude_unset=True)
    )
    return condition


@router.delete("/chart/{patient_id}/conditions/{condition_id}")
async def remove_tooth_condition(
    patient_id: str,
    condition_id: str,
    current_user: User = Depends(require_role(UserRole.DENTIST, UserRole.HYGIENIST, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Remove a tooth condition (e.g. if entered by mistake)"""
    p_uuid = uuid.UUID(patient_id)
    c_uuid = uuid.UUID(condition_id)
    result = await db.execute(
        select(ToothCondition).where(ToothCondition.id == c_uuid, ToothCondition.patient_id == p_uuid)
    )
    condition = result.scalar_one_or_none()
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
        
    db.delete(condition)
    await db.commit()
    return {"message": "Condition removed"}


@router.get("/chart/{patient_id}/history", response_model=Dict[str, List[ChartingEntryResponse]])
async def get_chart_history(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get the timeline of charting entries"""
    history = await ChartingService.get_chart_history(db, uuid.UUID(patient_id))
    return {"history": history}


@router.get("/chart/symbols/", response_model=Dict[str, List[ChartingSymbolResponse]])
async def list_charting_symbols(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List charting symbols for the practice"""
    result = await db.execute(
        select(ChartingSymbol).where(
            ChartingSymbol.practice_id == current_user.practice_id,
            ChartingSymbol.is_active == True
        )
    )
    return {"symbols": result.scalars().all()}


@router.post("/chart/symbols/", response_model=ChartingSymbolResponse)
async def create_charting_symbol(
    symbol_data: ChartingSymbolCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Create a new charting symbol"""
    symbol = ChartingSymbol(
        practice_id=current_user.practice_id,
        **symbol_data.dict()
    )
    db.add(symbol)
    await db.commit()
    await db.refresh(symbol)
    return symbol

# --- Perio Charting ---

@router.get("/perio/", response_model=PerioChartListResponse)
async def list_perio_charts(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> Any:
    """
    List periodontal charts for the practice or a specific patient
    """
    query = select(PerioChart)
    if patient_id:
        query = query.where(PerioChart.patient_id == patient_id)
        
    result = await db.execute(query)
    charts = result.scalars().all()
    
    # Filter by practice access
    filtered_charts = []
    for chart in charts:
        patient_result = await db.execute(
            select(Patient).where(Patient.id == chart.patient_id, Patient.practice_id == current_user.practice_id)
        )
        if patient_result.scalar_one_or_none():
            filtered_charts.append(chart)

    # HIPAA: Log full perio chart list fetching
    await log_audit_event(
        db, current_user, "list_perio_charts", "perio_chart", None, request
    )
    await db.commit()
    
    return PerioChartListResponse(
        perio_charts=filtered_charts,
        count=len(filtered_charts)
    )


@router.post("/perio/", response_model=PerioChartResponse)
async def create_perio_chart(
    chart_data: PerioChartCreate,
    current_user: User = Depends(require_role(UserRole.DENTIST, UserRole.HYGIENIST, UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new periodontal chart with entries
    """
    # Verify patient
    result = await db.execute(
        select(Patient).where(Patient.id == chart_data.patient_id, Patient.practice_id == current_user.practice_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or access denied",
        )
        
    chart = PerioChart(
        patient_id=chart_data.patient_id,
        provider_id=current_user.id,
        overall_bleeding_index=chart_data.overall_bleeding_index,
        plaque_index=chart_data.plaque_index,
        calculus_index=chart_data.calculus_index,
        diagnosis=chart_data.diagnosis,
        notes=chart_data.notes,
    )
    db.add(chart)
    await db.flush()  # To get chart.id
    
    for entry_data in chart_data.entries:
        entry_values = entry_data.model_dump()
        entry = PerioChartEntry(
            perio_chart_id=chart.id,
            tooth_number=str(entry_values["tooth_number"]),
            probing_depths=[
                entry_values.get("pd_mesiobuccal"),
                entry_values.get("pd_buccal"),
                entry_values.get("pd_distobuccal"),
                entry_values.get("pd_mesiolingual"),
                entry_values.get("pd_lingual"),
                entry_values.get("pd_distolingual"),
            ],
            bleeding_points=[
                entry_values.get("bop_mesiobuccal", False),
                entry_values.get("bop_buccal", False),
                entry_values.get("bop_distobuccal", False),
                entry_values.get("bop_mesiolingual", False),
                entry_values.get("bop_lingual", False),
                entry_values.get("bop_distolingual", False),
            ],
            attachment_level=[
                entry_values.get("cal_mesiobuccal"),
                entry_values.get("cal_buccal"),
                entry_values.get("cal_distobuccal"),
                entry_values.get("cal_mesiolingual"),
                entry_values.get("cal_lingual"),
                entry_values.get("cal_distolingual"),
            ],
            mobility=str(entry_values["mobility"]) if entry_values.get("mobility") is not None else None,
            furcation=entry_values.get("furcation_class"),
        )
        db.add(entry)
        
    await db.commit()
    await db.refresh(chart)
    return {
        "id": chart.id,
        "patient_id": chart.patient_id,
        "provider_id": chart.provider_id,
        "examination_date": chart.examination_date,
        "overall_bleeding_index": chart.overall_bleeding_index,
        "plaque_index": chart.plaque_index,
        "calculus_index": chart.calculus_index,
        "diagnosis": chart.diagnosis,
        "notes": chart.notes,
        "created_at": chart.created_at,
        "updated_at": chart.updated_at,
        "entries": [],
    }
