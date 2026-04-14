"""
Clinic Settings Endpoints
Practice/clinic configuration and settings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, cast, String
from sqlalchemy.orm import selectinload
from typing import Any

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.practice import Practice
from app.models.appointment import Chair, AppointmentType
from app.schemas.clinic import ClinicSettingsResponse, ClinicSettingsUpdate

router = APIRouter()


@router.get("/settings", response_model=ClinicSettingsResponse)
async def get_clinic_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get clinic/practice settings
    """
    # Get practice - cast UUID to string for SQLite compatibility
    stmt = select(Practice).where(cast(Practice.id, String) == str(current_user.practice_id))
    result = await db.execute(stmt)
    practice = result.scalar_one_or_none()
    
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")
    
    # Query chairs separately
    chairs_stmt = select(Chair).where(cast(Chair.practice_id, String) == str(practice.id))
    chairs_result = await db.execute(chairs_stmt)
    chairs_list = chairs_result.scalars().all()
    
    # Query appointment types separately
    appt_types_stmt = select(AppointmentType).where(cast(AppointmentType.practice_id, String) == str(practice.id))
    appt_types_result = await db.execute(appt_types_stmt)
    appt_types_list = appt_types_result.scalars().all()
    
    # Convert to dict format
    chairs_data = [
        {"id": str(chair.id), "name": chair.name, "enabled": chair.is_active}
        for chair in chairs_list
    ] if chairs_list else [
        {"id": "1", "name": "Chair 1", "enabled": True},
        {"id": "2", "name": "Chair 2", "enabled": True},
    ]
    
    appointment_types_data = [
        {"name": appt.name, "duration": appt.duration, "color": appt.color or "#3B82F6"}
        for appt in appt_types_list
    ] if appt_types_list else [
        {"name": "Checkup", "duration": 30, "color": "#3B82F6"},
        {"name": "Cleaning", "duration": 45, "color": "#10B981"},
        {"name": "Filling", "duration": 60, "color": "#F59E0B"},
        {"name": "Root Canal", "duration": 90, "color": "#EF4444"},
        {"name": "Extraction", "duration": 45, "color": "#8B5CF6"},
    ]
    
    return {
        "id": str(practice.id),
        "name": practice.name,
        "email": practice.email or "",
        "phone": practice.phone or "",
        "address": practice.address or "",
        "city": practice.city or "",
        "state": practice.state or "",
        "zipCode": practice.zip_code or "",
        "country": practice.country or "US",
        "timezone": practice.timezone or "America/New_York",
        "website": practice.website or "",
        "logo": practice.logo_url or "",
        "workingHours": practice.working_hours or {
            "monday": {"start": "09:00", "end": "17:00", "enabled": True},
            "tuesday": {"start": "09:00", "end": "17:00", "enabled": True},
            "wednesday": {"start": "09:00", "end": "17:00", "enabled": True},
            "thursday": {"start": "09:00", "end": "17:00", "enabled": True},
            "friday": {"start": "09:00", "end": "17:00", "enabled": True},
            "saturday": {"start": "09:00", "end": "13:00", "enabled": False},
            "sunday": {"start": "09:00", "end": "13:00", "enabled": False},
        },
        "appointmentTypes": appointment_types_data,
        "chairs": chairs_data,
    }


@router.put("/settings", response_model=ClinicSettingsResponse)
async def update_clinic_settings(
    settings: ClinicSettingsUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update clinic/practice settings
    """
    # Get practice
    stmt = select(Practice).where(Practice.id == current_user.practice_id)
    result = await db.execute(stmt)
    practice = result.scalar_one_or_none()
    
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")
    
    # Update fields
    update_data = settings.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Map camelCase to snake_case
        snake_field = field
        if field == "zipCode":
            snake_field = "zip_code"
        elif field == "workingHours":
            snake_field = "working_hours"
        elif field == "appointmentTypes":
            snake_field = "appointment_types"
        elif field == "logoUrl":
            snake_field = "logo_url"
            
        if hasattr(practice, snake_field):
            setattr(practice, snake_field, value)
    
    await db.commit()
    await db.refresh(practice)
    
    return {
        "id": str(practice.id),
        "name": practice.name,
        "email": practice.email or "",
        "phone": practice.phone or "",
        "address": practice.address or "",
        "city": practice.city or "",
        "state": practice.state or "",
        "zipCode": practice.zip_code or "",
        "country": practice.country or "US",
        "timezone": practice.timezone or "America/New_York",
        "website": practice.website or "",
        "logo": practice.logo_url or "",
        "workingHours": practice.working_hours or {},
        "appointmentTypes": practice.appointment_types or [],
        "chairs": practice.chairs or [],
    }
