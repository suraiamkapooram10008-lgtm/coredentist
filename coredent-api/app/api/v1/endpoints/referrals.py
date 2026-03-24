"""
Referral Endpoints
CRUD operations for referral management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user
from app.core.email import email_service
from app.models.user import User
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

router = APIRouter()


# Referral Source Endpoints

@router.get("/sources/")
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
        # Use parameterized query to prevent SQL injection
        search_pattern = f"%{search}%"
        query = query.where(ReferralSource1.name.ilike(search_pattern))
    
    query = query.order_by(ReferralSource1.name)
    
    result = await db.execute(query)
    sources = result.scalars().all()
    
    return {"sources": sources, "count": len(sources)}


@router.post("/sources/")
async def create_referral_source(
    source_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new referral source
    """
    source = ReferralSource1(
        practice_id=current_user.practice_id,
        **source_data
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    
    return source


# Referral Endpoints

@router.get("/")
async def list_referrals(
    status: Optional[ReferralStatus] = Query(None, description="Filter by status"),
    referral_type: Optional[ReferralType] = Query(None, description="Filter by type"),
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    source_id: Optional[str] = Query(None, description="Filter by source"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List referrals
    """
    query = select(Referral).where(Referral.practice_id == current_user.practice_id)
    
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
    
    return {"referrals": referrals, "count": len(referrals)}


@router.get("/{referral_id}")
async def get_referral(
    referral_id: str,
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
        )
    )
    referral = result.scalar_one_or_none()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found",
        )
    
    return referral


@router.post("/")
async def create_referral(
    referral_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new referral
    """
    # Verify patient exists
    patient_id = referral_data.get("patient_id")
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
    
    # Generate referral number
    today = datetime.now()
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
        referring_provider_id=current_user.id,
        referral_number=referral_number,
        **referral_data
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    
    return referral


@router.put("/{referral_id}")
async def update_referral(
    referral_id: str,
    referral_data: dict,
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
        )
    )
    referral = result.scalar_one_or_none()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found",
        )
    
    for field, value in referral_data.items():
        setattr(referral, field, value)
    
    # Update completed date if status changed to completed
    if referral_data.get("status") == ReferralStatus.COMPLETED and not referral.completed_date:
        referral.completed_date = datetime.utcnow()
    
    await db.commit()
    await db.refresh(referral)
    
    return referral


@router.delete("/{referral_id}")
async def delete_referral(
    referral_id: str,
    current_user: User = Depends(get_current_user),
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
        )
    )
    referral = result.scalar_one_or_none()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found",
        )
    
    await db.delete(referral)
    await db.commit()
    
    return {"message": "Referral deleted successfully"}


# Referral Communication Endpoints

@router.get("/{referral_id}/communications")
async def list_referral_communications(
    referral_id: str,
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
    referral_id: str,
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
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get referral summary statistics
    """
    query = select(Referral).where(Referral.practice_id == current_user.practice_id)
    
    if start_date:
        query = query.where(Referral.referral_date >= start_date)
    
    if end_date:
        query = query.where(Referral.referral_date <= end_date)
    
    result = await db.execute(query)
    referrals = result.scalars().all()
    
    # Calculate stats
    total = len(referrals)
    completed = sum(1 for r in referrals if r.status == ReferralStatus.COMPLETED)
    pending = sum(1 for r in referrals if r.status == ReferralStatus.PENDING)
    cancelled = sum(1 for r in referrals if r.status == ReferralStatus.CANCELLED)
    no_shows = sum(1 for r in referrals if r.status == ReferralStatus.NO_SHOW)
    
    # Calculate revenue
    total_fees = sum(float(r.referral_fee or 0) for r in referrals)
    collected_fees = sum(float(r.referral_fee or 0) for r in referrals if r.referral_received)
    
    return {
        "total_referrals": total,
        "completed": completed,
        "pending": pending,
        "cancelled": cancelled,
        "no_shows": no_shows,
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
    referral_id: str,
    email_data: ReferralEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Send email to referral specialist
    """
    # Verify referral exists
    result = await db.execute(
        select(Referral).where(
            Referral.id == referral_id,
            Referral.practice_id == current_user.practice_id,
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
    
    # Build email content
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Referral Communication</h2>
            <p><strong>From:</strong> {practice.name if practice else 'CoreDent Practice'}</p>
            <p><strong>Re:</strong> Patient Referral - {patient.first_name if patient else ''} {patient.last_name if patient else ''}</p>
            <hr>
            <div style="margin: 20px 0;">
                {email_data.message}
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
            notes=email_data.message,
        )
        db.add(communication)
        await db.commit()
        
        return {"message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )
