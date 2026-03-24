"""
Lab Endpoints
CRUD operations for lab case management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from typing import List, Optional, Any
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.lab import (
    Lab,
    LabCase,
    LabInvoice,
    LabCommunication,
    LabCaseStatus,
    LabCaseType,
)
from app.api.deps import verify_csrf

router = APIRouter()


# Lab Endpoints

@router.get("/vendors/")
async def list_labs(
    search: Optional[str] = Query(None, description="Search by name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_preferred: Optional[bool] = Query(None, description="Filter by preferred"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List dental labs
    """
    query = select(Lab).where(Lab.practice_id == current_user.practice_id)
    
    if is_active is not None:
        query = query.where(Lab.is_active == is_active)
    
    if is_preferred is not None:
        query = query.where(Lab.is_preferred == is_preferred)
    
    if search:
        # Use parameterized query to prevent SQL injection
        search_pattern = f"%{search}%"
        query = query.where(Lab.name.ilike(search_pattern))
    
    query = query.order_by(Lab.name)
    
    result = await db.execute(query)
    labs = result.scalars().all()
    
    return {"labs": labs, "count": len(labs)}


@router.post("/vendors/")
async def create_lab(
    lab_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new lab vendor
    """
    lab = Lab(
        practice_id=current_user.practice_id,
        **lab_data
    )
    db.add(lab)
    await db.commit()
    await db.refresh(lab)
    
    return lab


# Lab Case Endpoints

@router.get("/cases/")
async def list_lab_cases(
    status: Optional[LabCaseStatus] = Query(None, description="Filter by status"),
    case_type: Optional[LabCaseType] = Query(None, description="Filter by type"),
    lab_id: Optional[str] = Query(None, description="Filter by lab"),
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List lab cases
    """
    query = select(LabCase).where(LabCase.practice_id == current_user.practice_id)
    
    if status:
        query = query.where(LabCase.status == status)
    
    if case_type:
        query = query.where(LabCase.case_type == case_type)
    
    if lab_id:
        query = query.where(LabCase.lab_id == lab_id)
    
    if patient_id:
        query = query.where(LabCase.patient_id == patient_id)
    
    if start_date:
        query = query.where(LabCase.sent_date >= start_date)
    
    if end_date:
        query = query.where(LabCase.sent_date <= end_date)
    
    query = query.order_by(LabCase.sent_date.desc())
    
    result = await db.execute(query)
    cases = result.scalars().all()
    
    return {"cases": cases, "count": len(cases)}


@router.get("/cases/{case_id}")
async def get_lab_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get lab case by ID
    """
    result = await db.execute(
        select(LabCase).where(
            LabCase.id == case_id,
            LabCase.practice_id == current_user.practice_id,
        )
    )
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab case not found",
        )
    
    return case


@router.post("/cases/")
async def create_lab_case(
    case_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new lab case
    """
    # Verify patient exists
    patient_id = case_data.get("patient_id")
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
    
    # Generate case number
    today = datetime.now()
    count_result = await db.execute(
        select(func.count(LabCase.id)).where(
            LabCase.practice_id == current_user.practice_id,
            func.date(LabCase.created_at) == today.date()
        )
    )
    count = count_result.scalar() or 0
    case_number = f"CASE-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    
    lab_case = LabCase(
        practice_id=current_user.practice_id,
        provider_id=current_user.id,
        case_number=case_number,
        **case_data
    )
    db.add(lab_case)
    await db.commit()
    await db.refresh(lab_case)
    
    return lab_case


@router.put("/cases/{case_id}")
async def update_lab_case(
    case_id: str,
    case_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update lab case
    """
    result = await db.execute(
        select(LabCase).where(
            LabCase.id == case_id,
            LabCase.practice_id == current_user.practice_id,
        )
    )
    lab_case = result.scalar_one_or_none()
    
    if not lab_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab case not found",
        )
    
    for field, value in case_data.items():
        setattr(lab_case, field, value)
    
    # Auto-update timestamps based on status
    if case_data.get("status") == LabCaseStatus.SHIPPED and not lab_case.delivered_date:
        lab_case.delivered_date = datetime.utcnow()
    
    await db.commit()
    await db.refresh(lab_case)
    
    return lab_case


@router.delete("/cases/{case_id}")
async def delete_lab_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete lab case
    """
    result = await db.execute(
        select(LabCase).where(
            LabCase.id == case_id,
            LabCase.practice_id == current_user.practice_id,
        )
    )
    lab_case = result.scalar_one_or_none()
    
    if not lab_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab case not found",
        )
    
    await db.delete(lab_case)
    await db.commit()
    
    return {"message": "Lab case deleted successfully"}


# Lab Invoice Endpoints

@router.get("/invoices/")
async def list_lab_invoices(
    status: Optional[str] = Query(None, description="Filter by status"),
    lab_id: Optional[str] = Query(None, description="Filter by lab"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List lab invoices
    """
    query = select(LabInvoice).where(LabInvoice.practice_id == current_user.practice_id)
    
    if status:
        query = query.where(LabInvoice.status == status)
    
    if lab_id:
        query = query.where(LabInvoice.lab_id == lab_id)
    
    if start_date:
        query = query.where(LabInvoice.invoice_date >= start_date)
    
    if end_date:
        query = query.where(LabInvoice.invoice_date <= end_date)
    
    query = query.order_by(LabInvoice.invoice_date.desc())
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    return {"invoices": invoices, "count": len(invoices)}


@router.get("/invoices/{invoice_id}")
async def get_lab_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get lab invoice by ID
    """
    result = await db.execute(
        select(LabInvoice).where(
            LabInvoice.id == invoice_id,
            LabInvoice.practice_id == current_user.practice_id,
        )
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab invoice not found",
        )
    
    return invoice


# Lab Reports Endpoints

@router.get("/reports/summary")
async def get_lab_summary(
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get lab summary statistics
    """
    query = select(LabCase).where(LabCase.practice_id == current_user.practice_id)
    
    if start_date:
        query = query.where(LabCase.sent_date >= start_date)
    
    if end_date:
        query = query.where(LabCase.sent_date <= end_date)
    
    result = await db.execute(query)
    cases = result.scalars().all()
    
    # Calculate stats
    total = len(cases)
    pending = sum(1 for c in cases if c.status == LabCaseStatus.PENDING)
    in_progress = sum(1 for c in cases if c.status == LabCaseStatus.IN_PROGRESS)
    completed = sum(1 for c in cases if c.status == LabCaseStatus.COMPLETED)
    
    # Calculate costs
    total_cost = sum(float(c.case_cost or 0) for c in cases)
    total_charged = sum(float(c.patient_charge or 0) for c in cases)
    
    return {
        "total_cases": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "total_cost": total_cost,
        "total_charged": total_charged,
    }
