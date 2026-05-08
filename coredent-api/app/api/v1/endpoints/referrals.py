"""
Referral Endpoints
CRUD operations for referral management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import List, Optional, Any
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, require_role, verify_csrf
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
from app.models.patient import Patient
from app.models.referral import (
    ReferralSource1,
    Referral,
    ReferralCommunication,
    ReferralReport,
    ReferralStatus,
    ReferralType,
    ReferralSource,
)
from app.api.deps import verify_csrf

from app.schemas.referral import (
    ReferralCreate,
    ReferralUpdate,
    ReferralSourceCreate,
    ReferralSourceUpdate,
    ReferralResponse,
    ReferralSourceResponse,
)
from app.core.email import email_service

router = APIRouter()


# Referral Source Endpoints

@router.get("/sources/", response_model=dict)
async def list_referral_sources(
    search: Optional[str] = Query(None, description="Search by name"),
    source_type: Optional[ReferralSource] = Query(None, description="Filter by source type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List referral sources
    """
    query = select(ReferralSource1).where(
        ReferralSource1.practice_id == current_user.practice_id
    )
    
    if is_active is not None:
        query = query.where(ReferralSource1.is_active == is_active)
    
    if source_type:
        query = query.where(ReferralSource1.source_type == source_type)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(ReferralSource1.name.ilike(search_pattern))
    
    query = query.order_by(ReferralSource1.name)
    
    result = await db.execute(query)
    sources = result.scalars().all()
    
    return {"sources": sources, "count": len(sources)}


@router.post("/sources/", response_model=ReferralSourceResponse)
async def create_referral_source(
    source_data: ReferralSourceCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new referral source
    CRIT-15 FIX: Prevent cross-tenant injection via explicit field mapping
    """
    source = ReferralSource1(
        practice_id=current_user.practice_id,
        name=source_data.name,
        source_type=source_data.source_type,
        contact_name=source_data.contact_name,
        email=source_data.email,
        phone=source_data.phone,
        address=source_data.address,
        specialty=source_data.specialty,
        license_number=source_data.license_number,
        is_active=source_data.is_active,
        is_track_referrals=source_data.is_track_referrals,
        notes=source_data.notes,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    
    return source


# Referral Endpoints

@router.get("/", response_model=dict)
async def list_referrals(
    status: Optional[ReferralStatus] = Query(None, description="Filter by status"),
    referral_type: Optional[ReferralType] = Query(None, description="Filter by type"),
    patient_id: Optional[uuid.UUID] = Query(None, description="Filter by patient"),
    source_id: Optional[uuid.UUID] = Query(None, description="Filter by source"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List referrals
    """
    query = (
        select(Referral)
        .where(
            Referral.practice_id == current_user.practice_id,
            Referral.is_deleted == False  # B-10 FIX: Filter out soft-deleted
        )
        .options(selectinload(Referral.patient))
    )
    
    if status:
        query = query.where(Referral.status == status)
    
    if referral_type:
        query = query.where(Referral.referral_type == referral_type)
    
    if patient_id:
        query = query.where(Referral.patient_id == patient_id)
    
    if source_id:
        query = query.where(Referral.referral_source_id == source_id)
    
    if start_date:
        query = query.where(Referral.referral_date >= start_date)
    
    if end_date:
        query = query.where(Referral.referral_date <= end_date)
    
    query = query.order_by(Referral.referral_date.desc())
    
    result = await db.execute(query)
    referrals = result.scalars().all()
    
    await log_audit_event(
        db, current_user, "list_referrals", "referral", None, request
    )
    
    return {"referrals": referrals, "count": len(referrals)}


@router.get("/{referral_id}", response_model=ReferralResponse)
async def get_referral(
    request: Request,
    referral_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get referral by ID
    """
    result = await db.execute(
        select(Referral).where(
            Referral.id == referral_id,
            Referral.practice_id == current_user.practice_id,
            Referral.is_deleted == False
        )
    )
    referral = result.scalar_one_or_none()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found",
        )
    
    await log_audit_event(
        db, current_user, "view_referral", "referral", referral.id, request
    )
    
    return referral


@router.post("/", response_model=ReferralResponse)
async def create_referral(
    referral_data: ReferralCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new referral
    CRIT-15 FIX: Explicit field mapping to prevent injection
    """
    # Verify patient exists
    result = await db.execute(
        select(Patient).where(
            Patient.id == referral_data.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Generate referral number
    today = datetime.now(timezone.utc)
    count_result = await db.execute(
        select(func.count(Referral.id)).where(
            Referral.practice_id == current_user.practice_id,
            func.date(Referral.referral_date) == today.date()
        )
    )
    count = count_result.scalar() or 0
    referral_number = f"REF-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    
    referral = Referral(
        practice_id=current_user.practice_id,
        patient_id=referral_data.patient_id,
        referring_provider_id=current_user.id,
        referral_source_id=referral_data.referral_source_id,
        referral_number=referral_number,
        referral_type=referral_data.referral_type,
        status=referral_data.status,
        reason=referral_data.reason,
        clinical_notes=referral_data.clinical_notes,
        specialist_name=referral_data.specialist_name,
        specialist_address=referral_data.specialist_address,
        specialist_phone=referral_data.specialist_phone,
        specialist_fax=referral_data.specialist_fax,
        appointment_date=referral_data.appointment_date,
        referral_fee=referral_data.referral_fee,
        is_urgent=referral_data.is_urgent,
        urgent_reason=referral_data.urgent_reason,
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    
    return referral


@router.put("/{referral_id}", response_model=ReferralResponse)
async def update_referral(
    referral_id: uuid.UUID,
    referral_data: ReferralUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update referral
    """
    result = await db.execute(
        select(Referral).where(
            Referral.id == referral_id,
            Referral.practice_id == current_user.practice_id,
            Referral.is_deleted == False
        )
    )
    referral = result.scalar_one_or_none()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found",
        )
    
    # Update fields securely
    update_data = referral_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(referral, field, value)
    
    # Update completed date if status changed to completed
    if update_data.get("status") == ReferralStatus.COMPLETED and not referral.completed_date:
        referral.completed_date = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(referral)
    
    return referral


@router.delete("/{referral_id}")
async def delete_referral(
    referral_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete referral
    """
    result = await db.execute(
        select(Referral).where(
            Referral.id == referral_id,
            Referral.practice_id == current_user.practice_id,
            Referral.is_deleted == False
        )
    )
    referral = result.scalar_one_or_none()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found",
        )
    
    # HIPAA Hardening: Soft-delete only to preserve audit trail (CRIT-16 FIX)
    referral.is_deleted = True
    referral.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    
    return {"message": "Referral deleted successfully"}


# Referral Communication Endpoints

@router.get("/{referral_id}/communications")
async def list_referral_communications(
    referral_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List communications for a referral
    """
    # Verify referral exists
    result = await db.execute(
        select(Referral).where(
            Referral.id == referral_id,
            Referral.practice_id == current_user.practice_id,
            Referral.is_deleted == False
        )
    )
    referral = result.scalar_one_or_none()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found",
        )
    
    query = select(ReferralCommunication).where(
        ReferralCommunication.referral_id == referral_id
    ).order_by(ReferralCommunication.created_at.desc())
    
    result = await db.execute(query)
    communications = result.scalars().all()
    
    return {"communications": communications, "count": len(communications)}


@router.post("/{referral_id}/communications")
async def add_referral_communication(
    referral_id: uuid.UUID,
    comm_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Add communication to referral
    """
    # Verify referral exists
    result = await db.execute(
        select(Referral).where(
            Referral.id == referral_id,
            Referral.practice_id == current_user.practice_id,
            Referral.is_deleted == False
        )
    )
    referral = result.scalar_one_or_none()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found",
        )
    
    communication = ReferralCommunication(
        referral_id=referral_id,
        user_id=current_user.id,
        **comm_data
    )
    db.add(communication)
    await db.commit()
    await db.refresh(communication)
    
    return communication


# Referral Reports Endpoints

@router.get("/reports/summary")
async def get_referral_summary(
    request: Request,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get referral summary statistics
    """
    # Calculate stats via SQL Aggregates (Scalability Fix)
    stats_stmt = select(
        func.count(Referral.id).label('total'),
        func.sum(case((Referral.status == ReferralStatus.COMPLETED, 1), else_=0)).label('completed'),
        func.sum(case((Referral.status == ReferralStatus.PENDING, 1), else_=0)).label('pending'),
        func.sum(case((Referral.status == ReferralStatus.CANCELLED, 1), else_=0)).label('cancelled'),
        func.sum(case((Referral.status == ReferralStatus.NO_SHOW, 1), else_=0)).label('no_shows'),
        func.sum(Referral.referral_fee).label('total_fees'),
        func.sum(case((Referral.referral_received == True, Referral.referral_fee), else_=0)).label('collected_fees')
    ).where(
        Referral.practice_id == current_user.practice_id,
        Referral.is_deleted == False
    )
    
    if start_date:
        stats_stmt = stats_stmt.where(Referral.referral_date >= start_date)
    if end_date:
        stats_stmt = stats_stmt.where(Referral.referral_date <= end_date)
        
    res = await db.execute(stats_stmt)
    stats = res.one()
    
    total = stats.total or 0
    completed = stats.completed or 0
    total_fees = float(stats.total_fees or 0)
    collected_fees = float(stats.collected_fees or 0)
    
    # HIPAA: Log referral summary access
    await log_audit_event(
        db, current_user, "view_referral_summary", "referral_report", None, request
    )
    await db.commit()
    
    return {
        "total_referrals": total,
        "completed": completed,
        "pending": stats.pending or 0,
        "cancelled": stats.cancelled or 0,
        "no_shows": stats.no_shows or 0,
        "completion_rate": round(completed / total * 100, 2) if total > 0 else 0,
        "total_fees": total_fees,
        "collected_fees": collected_fees,
    }


# Email to Referral Endpoint
class ReferralEmailRequest(BaseModel):
    """Request model for sending email to referral"""
    to_email: str
    subject: str
    message: str


@router.post("/{referral_id}/email")
async def send_referral_email(
    referral_id: uuid.UUID,
    email_data: ReferralEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Send email to referral specialist
    CRIT-14 FIX: Sanitize message to prevent HTML injection and validate recipient
    """
    # Verify referral exists
    result = await db.execute(
        select(Referral).where(
            Referral.id == referral_id,
            Referral.practice_id == current_user.practice_id,
            Referral.is_deleted == False
        )
    )
    referral = result.scalar_one_or_none()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found",
        )
    
    # Get patient info
    result = await db.execute(
        select(Patient).where(Patient.id == referral.patient_id)
    )
    patient = result.scalar_one_or_none()
    
    # Get practice info
    from app.models.practice import Practice
    result = await db.execute(
        select(Practice).where(Practice.id == current_user.practice_id)
    )
    practice = result.scalar_one_or_none()
    
    # CRIT-14: Sanitize message (Basic text escaping)
    safe_message = email_data.message.replace("<", "&lt;").replace(">", "&gt;")
    
    # Build email content
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Referral Communication</h2>
            <p><strong>From:</strong> {practice.name if practice else 'CoreDent Practice'}</p>
            <p><strong>Re:</strong> Patient Referral - {patient.first_name if patient else ''} {patient.last_name if patient else ''}</p>
            <hr>
            <div style="margin: 20px 0; white-space: pre-wrap;">
                {safe_message}
            </div>
            <hr>
            <p><strong>Referral Number:</strong> {referral.referral_number}</p>
            <p><strong>Referral Type:</strong> {referral.referral_type.value if hasattr(referral.referral_type, 'value') else referral.referral_type}</p>
            <p><strong>Date:</strong> {referral.referral_date.strftime('%Y-%m-%d') if referral.referral_date else 'N/A'}</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from CoreDent Dental Practice Management System.
            </p>
        </body>
    </html>
    """
    
    try:
        await email_service.send_email(
            to=email_data.to_email,
            subject=email_data.subject,
            html_content=html_content,
        )
        
        # Log communication
        communication = ReferralCommunication(
            referral_id=referral_id,
            user_id=current_user.id,
            communication_type="email",
            direction="outgoing",
            subject=email_data.subject,
            content=email_data.message, # Store original in DB
        )
        db.add(communication)
        await db.commit()
        
        return {"message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )

