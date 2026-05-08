"""
Appointment Endpoints
CRUD operations for appointments
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Any, Union
from uuid import UUID
import asyncio

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.appointment import Appointment, AppointmentStatus, AppointmentTypeEnum, Chair
from app.models.patient import Patient
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentListResponse,
    AppointmentSlot,
)
from app.api.deps import verify_csrf

router = APIRouter()


async def _execute(db: Union[AsyncSession, Session], query):
    """Execute a SQLAlchemy query on either async or sync session."""
    result = db.execute(query)
    if asyncio.iscoroutine(result):
        result = await result
    return result


@router.get("/", response_model=AppointmentListResponse)
async def list_appointments(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    status: Optional[AppointmentStatus] = Query(None, description="Filter by status"),
    provider_id: Optional[UUID] = Query(None, description="Filter by provider"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List appointments with optional filters
    """
    # Build query
    query = select(Appointment).where(Appointment.practice_id == current_user.practice_id)
    
    # Apply filters
    if start_date:
        query = query.where(Appointment.start_time >= start_date)
    if end_date:
        query = query.where(Appointment.start_time <= end_date)
    if status:
        query = query.where(Appointment.status == status)
    if provider_id:
        query = query.where(Appointment.provider_id == provider_id)
    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)
    
    # Order by start time
    query = query.order_by(Appointment.start_time)
    
    result = await _execute(db, query)
    appointments = result.scalars().all()
    
    return AppointmentListResponse(
        appointments=appointments,
        count=len(appointments),
    )




@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get appointment by ID
    """
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.practice_id == current_user.practice_id,
        )
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    
    return appointment


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new appointment
    """
    # Verify patient exists and belongs to practice
    result = await _execute(
        db,
        select(Patient).where(
            Patient.id == appointment_data.patient_id,
            Patient.practice_id == current_user.practice_id,
        ),
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Check for scheduling conflicts
    chair_id_for_query = appointment_data.chair_id
    if chair_id_for_query and not isinstance(chair_id_for_query, UUID):
        try:
            chair_id_for_query = UUID(chair_id_for_query)
        except ValueError:
            chair_id_for_query = None

    # Lock the chair record to prevent concurrent bookings in the same operatory (B-13 FIX)
    if chair_id_for_query:
        # Use select for update to lock the chair row until the current transaction commits
        lock_query = select(Chair).where(Chair.id == chair_id_for_query).with_for_update()
        await _execute(db, lock_query)

    conflict_query = select(Appointment).where(
        Appointment.practice_id == current_user.practice_id,
        Appointment.start_time < appointment_data.end_time,
        Appointment.end_time > appointment_data.start_time,
        Appointment.status != AppointmentStatus.CANCELLED,
    )
    
    if appointment_data.provider_id:
        conflict_query = conflict_query.where(Appointment.provider_id == appointment_data.provider_id)
    
    if chair_id_for_query:
        conflict_query = conflict_query.where(Appointment.chair_id == chair_id_for_query)
    
    result = await _execute(db, conflict_query)
    conflicts = result.scalars().all()
    
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scheduling conflict detected",
        )
    
    # Create appointment
    # Calculate duration in minutes
    duration_minutes = appointment_data.duration or int((appointment_data.end_time - appointment_data.start_time).total_seconds() / 60)
    
    # Map string chair_id to UUID if needed
    chair_id = appointment_data.chair_id
    if chair_id and not isinstance(chair_id, UUID):
        try:
            chair_id = UUID(chair_id)
        except ValueError:
            chair_id = None
    
    # Map status if provided
    appt_status = AppointmentStatus.SCHEDULED
    if appointment_data.status:
        try:
            appt_status = AppointmentStatus(appointment_data.status)
        except ValueError:
            pass
    
    appointment = Appointment(
        practice_id=current_user.practice_id,
        patient_id=appointment_data.patient_id,
        provider_id=appointment_data.provider_id,
        chair_id=chair_id,
        appointment_type=appointment_data.appointment_type,
        status=appt_status,
        start_time=appointment_data.start_time,
        end_time=appointment_data.end_time,
        duration=duration_minutes,
        notes=appointment_data.notes,
    )
    
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update appointment
    """
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.practice_id == current_user.practice_id,
        )
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    
    # Check for scheduling conflicts (excluding current appointment)
    if appointment_data.start_time or appointment_data.end_time:
        start_time = appointment_data.start_time or appointment.start_time
        end_time = appointment_data.end_time or appointment.end_time
        
        conflict_query = select(Appointment).where(
            Appointment.practice_id == current_user.practice_id,
            Appointment.id != appointment_id,
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
            Appointment.status != AppointmentStatus.CANCELLED,
        )
        
        if appointment_data.provider_id or appointment.provider_id:
            provider_id = appointment_data.provider_id or appointment.provider_id
            conflict_query = conflict_query.where(Appointment.provider_id == provider_id)
        
        if appointment_data.chair_id or appointment.chair_id:
            chair_id = appointment_data.chair_id or appointment.chair_id
            conflict_query = conflict_query.where(Appointment.chair_id == chair_id)
        
        result = await db.execute(conflict_query)
        conflicts = result.scalars().all()
        
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Scheduling conflict detected",
            )
    
    # Update fields
    update_data = appointment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'chair_id' and value and not isinstance(value, UUID):
            try:
                value = UUID(value)
            except ValueError:
                continue
        if field == 'status' and value:
            try:
                value = AppointmentStatus(value)
            except ValueError:
                continue
        setattr(appointment, field, value)
    
    await db.commit()
    await db.refresh(appointment)
    
    return appointment


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def patch_appointment(
    appointment_id: UUID,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Partial update appointment"""
    return await update_appointment(
        appointment_id=appointment_id,
        appointment_data=appointment_data,
        current_user=current_user,
        db=db,
        _csrf=_csrf,
    )


@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: UUID,
    cancel_data: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Cancel an appointment"""
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.practice_id == current_user.practice_id,
        )
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    
    appointment.status = AppointmentStatus.CANCELLED
    if cancel_data:
        appointment.cancellation_reason = cancel_data.get("reason") or cancel_data.get("cancellation_reason")
    
    await db.commit()
    await db.refresh(appointment)
    
    return {"message": "Appointment cancelled successfully", "status": "cancelled", "id": str(appointment.id)}


@router.post("/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Complete an appointment"""
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.practice_id == current_user.practice_id,
        )
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    
    appointment.status = AppointmentStatus.COMPLETED
    await db.commit()
    await db.refresh(appointment)
    
    return {"message": "Appointment completed successfully", "status": "completed", "id": str(appointment.id)}


@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete appointment (soft delete by cancelling)
    """
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.practice_id == current_user.practice_id,
        )
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    
    # Soft delete by cancelling
    appointment.status = AppointmentStatus.CANCELLED
    await db.commit()
    
    return {"message": "Appointment cancelled successfully"}


@router.get("/availability", response_model=List[AppointmentSlot])
async def get_available_slots(
    date: Optional[str] = Query(None, description="Date to check availability (ISO format)"),
    duration: int = Query(30, description="Appointment duration in minutes"),
    provider_id: Optional[str] = Query(None, description="Filter by provider"),
    chair_id: Optional[str] = Query(None, description="Filter by chair"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get available appointment slots
    """
    # Parse date string if provided
    if date:
        try:
            parsed_date = datetime.fromisoformat(date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid date format. Use ISO format (YYYY-MM-DD).",
            )
    else:
        parsed_date = datetime.now(timezone.utc)
    
    # Define business hours (9 AM to 5 PM)
    start_hour = 9
    end_hour = 17
    
    # Calculate day boundaries for query
    day_start = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    
    # Convert string IDs to UUID
    provider_uuid = None
    if provider_id:
        try:
            provider_uuid = UUID(provider_id)
        except ValueError:
            pass
    chair_uuid = None
    if chair_id:
        try:
            chair_uuid = UUID(chair_id)
        except ValueError:
            pass
    
    # PERFORMANCE OPTIMIZATION: Fetch all appointments for the day in a single query
    # instead of querying inside the loop.
    query = select(Appointment).where(
        Appointment.practice_id == current_user.practice_id,
        Appointment.start_time >= day_start,
        Appointment.start_time < day_end,
        Appointment.status != AppointmentStatus.CANCELLED,
    )
    
    if provider_uuid:
        query = query.where(Appointment.provider_id == provider_uuid)
    if chair_uuid:
        query = query.where(Appointment.chair_id == chair_uuid)
        
    result = await db.execute(query)
    day_appointments = result.scalars().all()
    
    # Generate slots for the day
    slots = []
    current_time = parsed_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    business_end_time = parsed_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    
    while current_time + timedelta(minutes=duration) <= business_end_time:
        slot_end = current_time + timedelta(minutes=duration)
        
        # Check if slot is available (in-memory overlap check)
        is_available = True
        for apt in day_appointments:
            # Overlap condition: start1 < end2 AND end1 > start2
            if current_time < apt.end_time and slot_end > apt.start_time:
                is_available = False
                break
        
        if is_available:
            slots.append(AppointmentSlot(
                start_time=current_time,
                end_time=slot_end,
                duration=duration,
                is_available=True,
            ))
        
        current_time += timedelta(minutes=15)  # 15 minute intervals
    
    return slots
