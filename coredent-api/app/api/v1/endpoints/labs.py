"""
Lab Endpoints
CRUD operations for lab case management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
from app.models.patient import Patient
from app.models.lab import (
    Lab,
    LabCase,
    LabInvoice,
    LabCaseStatus,
    LabCaseType,
)
from app.api.deps import verify_csrf

router = APIRouter()


def _case_to_dict(case: LabCase) -> dict:
    """Serialize a LabCase to a dict for JSON response."""
    return {
        "id": str(case.id),
        "practice_id": str(case.practice_id),
        "lab_id": str(case.lab_id),
        "patient_id": str(case.patient_id),
        "provider_id": str(case.provider_id),
        "case_number": case.case_number,
        "case_type": case.case_type.value if case.case_type else None,
        "status": case.status.value if case.status else None,
        "description": case.description,
        "shade": case.shade,
        "shade_notes": case.shade_notes,
        "teeth_involved": case.teeth_involved,
        "sent_date": case.sent_date.isoformat() if case.sent_date else None,
        "due_date": case.due_date.isoformat() if case.due_date else None,
        "received_date": case.received_date.isoformat() if case.received_date else None,
        "delivered_date": case.delivered_date.isoformat() if case.delivered_date else None,
        "case_cost": str(case.case_cost) if case.case_cost is not None else None,
        "case_price": str(case.case_price) if case.case_price is not None else None,
        "patient_charge": str(case.patient_charge) if case.patient_charge is not None else None,
        "insurance_estimate": str(case.insurance_estimate) if case.insurance_estimate is not None else None,
        "tracking_number": case.tracking_number,
        "shipping_method": case.shipping_method,
        "shipping_cost": str(case.shipping_cost) if case.shipping_cost is not None else None,
        "is_deleted": case.is_deleted,
        "provider_notes": case.provider_notes,
        "lab_notes": case.lab_notes,
        "internal_notes": case.internal_notes,
        "prescriptions": case.prescriptions,
        "impressions": case.impressions,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
    }


# Lab Endpoints

@router.get("/vendors/")
async def list_labs(
    request: Request,
    search: Optional[str] = Query(None, description="Search by name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_preferred: Optional[bool] = Query(None, description="Filter by preferred"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List dental labs
    """
    query = select(Lab).where(
        Lab.practice_id == current_user.practice_id,
        Lab.is_deleted == False
    )

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

    # HIPAA: Log lab vendor list access
    await log_audit_event(
        db, current_user, "list_labs", "lab", None, request
    )
    await db.commit()

    return {"labs": labs, "count": len(labs)}


@router.post("/vendors/")
async def create_lab(
    lab_data: dict,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> dict:
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
    request: Request,
    status: Optional[LabCaseStatus] = Query(None, description="Filter by status"),
    case_type: Optional[LabCaseType] = Query(None, description="Filter by type"),
    lab_id: Optional[str] = Query(None, description="Filter by lab"),
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List lab cases
    """
    query = select(LabCase).where(
        LabCase.practice_id == current_user.practice_id,
        LabCase.is_deleted == False
    )

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

    # HIPAA: Log lab cases list access
    await log_audit_event(
        db, current_user, "list_lab_cases", "lab_case", None, request
    )
    await db.commit()

    return {"cases": [_case_to_dict(c) for c in cases], "count": len(cases)}


@router.get("/cases/{case_id}")
async def get_lab_case(
    request: Request,
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get lab case by ID
    """
    result = await db.execute(
        select(LabCase).where(
            LabCase.id == case_id,
            LabCase.practice_id == current_user.practice_id,
            LabCase.is_deleted == False,
        )
    )
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab case not found",
        )

    # HIPAA: Log lab case access
    await log_audit_event(
        db, current_user, "view_lab_case", "lab_case", case.id, request
    )
    await db.commit()

    return _case_to_dict(case)


@router.post("/cases/")
async def create_lab_case(
    case_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> dict:
    """
    Create new lab case
    """
    # Verify patient exists
    patient_id_str = case_data.get("patient_id")
    patient_id = uuid.UUID(patient_id_str) if isinstance(patient_id_str, str) else patient_id_str
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

    # Convert string IDs to UUID before model instantiation
    sanitized_data = dict(case_data)
    for uid_field in ("lab_id", "patient_id", "provider_id"):
        val = sanitized_data.get(uid_field)
        if isinstance(val, str):
            sanitized_data[uid_field] = uuid.UUID(val)

    lab_case = LabCase(
        practice_id=current_user.practice_id,
        provider_id=current_user.id,
        case_number=case_number,
        **sanitized_data
    )
    db.add(lab_case)
    await db.commit()
    await db.refresh(lab_case)

    return _case_to_dict(lab_case)


@router.put("/cases/{case_id}")
async def update_lab_case(
    case_id: uuid.UUID,
    case_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> dict:
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
        lab_case.delivered_date = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(lab_case)

    return _case_to_dict(lab_case)


@router.delete("/cases/{case_id}")
async def delete_lab_case(
    request: Request,
    case_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> dict:
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

    # HIPAA HARDENING: Use soft-delete to preserve clinical audit trail
    lab_case.is_deleted = True
    lab_case.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Lab case deleted successfully"}


# Lab Invoice Endpoints

@router.get("/invoices/")
async def list_lab_invoices(
    status: Optional[str] = Query(None, description="Filter by status"),
    lab_id: Optional[str] = Query(None, description="Filter by lab"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
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

    # HIPAA: Log lab invoices list access
    await log_audit_event(
        db, current_user, "list_lab_invoices", "lab_invoice", None, request
    )
    await db.commit()

    return {"invoices": invoices, "count": len(invoices)}


@router.get("/invoices/{invoice_id}")
async def get_lab_invoice(
    request: Request,
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
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

    # HIPAA: Log lab invoice access
    await log_audit_event(
        db, current_user, "view_lab_invoice", "lab_invoice", invoice.id, request
    )
    await db.commit()

    return invoice


# Lab Reports Endpoints

@router.get("/reports/summary")
async def get_lab_summary(
    request: Request,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict:
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

    # HIPAA: Log lab summary access
    await log_audit_event(
        db, current_user, "view_lab_summary", "lab_report", None, request
    )
    await db.commit()

    return {
        "total_cases": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "total_cost": total_cost,
        "total_charged": total_charged,
    }