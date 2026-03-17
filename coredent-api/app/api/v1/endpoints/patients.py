"""
Patient Endpoints
CRUD operations for patients
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Any
from uuid import UUID

from app.core.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListItem,
)
from app.api.deps import get_current_user, get_current_practice_id, Pagination, verify_csrf
from app.core.audit import log_audit_event
from fastapi import Request

router = APIRouter()


@router.get("", response_model=List[PatientListItem])
async def list_patients(
    request: Request,
    query: str = Query(None, description="Search by name, email, or phone"),
    status_filter: str = Query(None, alias="status"),
    pagination: Pagination = Depends(),
    practice_id: UUID = Depends(get_current_practice_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List patients with search and filtering
    """
    # HIPAA: Log PHI list access
    await log_audit_event(
        db, current_user, "patient_list_viewed", "patient", None, request
    )
    await db.commit()
    # Build query
    stmt = select(Patient).where(Patient.practice_id == practice_id)
    
    # Apply search
    if query:
        search_filter = or_(
            Patient.first_name.ilike(f"%{query}%"),
            Patient.last_name.ilike(f"%{query}%"),
            Patient.email.ilike(f"%{query}%"),
            Patient.phone.ilike(f"%{query}%"),
        )
        stmt = stmt.where(search_filter)
    
    # Apply status filter
    if status_filter:
        stmt = stmt.where(Patient.status == status_filter)
    
    # Apply pagination
    stmt = stmt.offset(pagination.offset).limit(pagination.limit)
    
    # Execute query
    result = await db.execute(stmt)
    patients = result.scalars().all()
    
    return patients


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: Request,
    patient_in: PatientCreate,
    practice_id: UUID = Depends(get_current_practice_id),
    current_user: User = Depends(get_current_user),
    _csrf: bool = Depends(verify_csrf),  # SECURITY FIX: CSRF protection
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create new patient
    """
    # Create patient
    patient = Patient(
        practice_id=practice_id,
        **patient_in.model_dump(),
    )
    
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    
    # HIPAA: Log creation
    await log_audit_event(
        db, current_user, "patient_created", "patient", patient.id, request
    )
    await db.commit()
    
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    request: Request,
    patient_id: UUID,
    practice_id: UUID = Depends(get_current_practice_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get patient by ID
    """
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # HIPAA: Log PHI read access
    await log_audit_event(
        db, current_user, "patient_viewed", "patient", patient.id, request
    )
    await db.commit()
    
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    request: Request,
    patient_id: UUID,
    patient_in: PatientUpdate,
    practice_id: UUID = Depends(get_current_practice_id),
    current_user: User = Depends(get_current_user),
    _csrf: bool = Depends(verify_csrf),  # SECURITY FIX: CSRF protection
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update patient
    """
    # Get patient
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Update fields
    update_data = patient_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    await db.commit()
    await db.refresh(patient)
    
    # HIPAA: Log patient update
    await log_audit_event(
        db, current_user, "patient_updated", "patient", patient.id, request
    )
    await db.commit()
    
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    request: Request,
    patient_id: UUID,
    practice_id: UUID = Depends(get_current_practice_id),
    current_user: User = Depends(get_current_user),
    _csrf: bool = Depends(verify_csrf),  # SECURITY FIX: CSRF protection
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete patient (soft delete by setting status to inactive)
    """
    # Get patient
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Soft delete
    patient.status = "inactive"
    await db.commit()
    
    # HIPAA: Log patient deletion (soft delete)
    await log_audit_event(
        db, current_user, "patient_deleted", "patient", patient.id, request
    )
    await db.commit()
