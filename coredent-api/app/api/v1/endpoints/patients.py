"""
Patient Endpoints
CRUD operations for patients
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from typing import List, Any
from uuid import UUID

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, PatientListItem
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, get_current_practice_id, Pagination, verify_csrf, require_role
from app.core.audit import log_audit_event
from app.core.sanitization import sanitize_search_query, sanitize_phone
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
import re

router = APIRouter()


@router.get("", response_model=PaginatedResponse[PatientListItem])
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
    List patients with search and filtering (paginated)
    """
    # HIPAA: Log PHI list access
    await log_audit_event(
        db, current_user, "patient_list_viewed", "patient", None, request
    )
    await db.commit()

    # Build base query with eager loading to prevent N+1 for visit stats
    base_stmt = (
        select(Patient)
        .where(Patient.practice_id == practice_id)
        .options(selectinload(Patient.appointments))
    )
    
    # Apply search - Use parameterized queries to prevent SQL injection
    if query:
        # HIGH-04 FIX: Sanitize search input
        query = sanitize_search_query(query)
        
        if query:
            # Normalize search pattern
            search_pattern = f"%{query}%"
            filters = [
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.email.ilike(search_pattern),
            ]
            
            # Expert Hardening: Smart Phone Search (strip formatting)
            clean_phone = re.sub(r"\D", "", query)
            if clean_phone:
                filters.append(Patient.phone.like(f"%{clean_phone}%"))
            else:
                filters.append(Patient.phone.ilike(search_pattern))
                
            base_stmt = base_stmt.where(or_(*filters))
    
    # Apply status filter
    if status_filter:
        base_stmt = base_stmt.where(Patient.status == status_filter)

    # Get total count BEFORE pagination
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(Patient).where(Patient.practice_id == practice_id)
    if query:
        query = sanitize_search_query(query)
        if query:
            search_pattern = f"%{query}%"
            count_filters = [
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.email.ilike(search_pattern),
            ]
            clean_phone = re.sub(r"\D", "", query)
            if clean_phone:
                count_filters.append(Patient.phone.like(f"%{clean_phone}%"))
            else:
                count_filters.append(Patient.phone.ilike(search_pattern))
            count_stmt = count_stmt.where(or_(*count_filters))
    if status_filter:
        count_stmt = count_stmt.where(Patient.status == status_filter)
    
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # Apply pagination to data query
    stmt = base_stmt.offset(pagination.offset).limit(pagination.limit)
    
    # Execute query
    result = await db.execute(stmt)
    patients = result.scalars().all()
    
    # Return paginated response
    return PaginatedResponse.create(
        items=patients,
        total=total,
        page=pagination.page,
        limit=pagination.limit
    )


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
    Create new patient (includes integrity check for duplicates)
    """
    # Expert Integrity: Check for duplicate patient in the same practice
    duplicate_query = select(Patient).where(
        Patient.practice_id == practice_id,
        or_(
            Patient.email == patient_in.email,
            Patient.phone == patient_in.phone
        )
    )
    result = await db.execute(duplicate_query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A patient with this email or phone already exists in this practice. Please verify the record."
        )

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
    
    # EXPERT HARDENING: Adaptive PHI Visibility (Least Privilege)
    # Front-Desk and Hygienists don't need access to specific insurance IDs/keys unless authorized.
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST]:
        # Redact the JSON content of insurance_info if present
        if patient.insurance_info:
             patient.insurance_info = {"status": "present", "redacted": True, "note": "Contact Admin for details"}
    
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
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
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
