"""
Prescription Endpoints
CRUD operations for prescription management, drug interaction checking,
allergy management, and medication tracking.
HIPAA: All prescription operations are audit-logged.
DEA: Controlled substance prescriptions tracked separately.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timezone, date
from typing import List, Optional, Any
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_user, require_role, verify_csrf
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
from app.models.prescription import (
    Prescription,
    Medication,
    PatientAllergy,
    PatientMedication,
    PrescriptionTemplate,
    DrugInteraction,
    PrescriptionStatus,
)
from app.models.patient import Patient
from app.schemas.prescription import (
    PrescriptionCreate,
    PrescriptionUpdate,
    PrescriptionCancel,
    PrescriptionResponse,
    PatientAllergyCreate,
    PatientAllergyUpdate,
    PatientAllergyResponse,
    PatientMedicationCreate,
    PatientMedicationUpdate,
    PatientMedicationResponse,
    PrescriptionTemplateCreate,
    PrescriptionTemplateResponse,
    InteractionCheckRequest,
    InteractionCheckResponse,
)
from app.services.prescription_service import PrescriptionService

router = APIRouter()


# ============================================
# PRESCRIPTION ENDPOINTS
# ============================================

@router.get("/")
async def list_prescriptions(
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    provider_id: Optional[str] = Query(None, description="Filter by provider"),
    is_controlled: Optional[bool] = Query(None, description="Filter controlled substances"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List prescriptions for the practice"""
    query = select(Prescription).where(
        Prescription.practice_id == current_user.practice_id
    )

    if patient_id:
        query = query.where(Prescription.patient_id == patient_id)
    if status_filter:
        query = query.where(Prescription.status == status_filter)
    if provider_id:
        query = query.where(Prescription.provider_id == provider_id)
    if is_controlled is not None:
        query = query.where(Prescription.is_controlled == is_controlled)
    if start_date:
        query = query.where(Prescription.prescribed_date >= start_date)
    if end_date:
        query = query.where(Prescription.prescribed_date <= end_date)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    offset = (page - 1) * limit
    query = query.order_by(Prescription.prescribed_date.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    prescriptions = result.scalars().all()

    # Audit log
    await log_audit_event(
        db, current_user, "list_prescriptions", "prescription", None, request
    )
    await db.commit()

    return {"prescriptions": prescriptions, "count": total, "page": page, "limit": limit}


@router.get("/{prescription_id:uuid}", response_model=PrescriptionResponse)
async def get_prescription(
    prescription_id: UUID,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get prescription by ID"""
    result = await db.execute(
        select(Prescription).where(
            Prescription.id == prescription_id,
            Prescription.practice_id == current_user.practice_id,
        )
    )
    prescription = result.scalar_one_or_none()

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    # Audit log (HIPAA: track all prescription access)
    await log_audit_event(
        db, current_user, "view_prescription", "prescription", prescription.id, request
    )
    await db.commit()

    return prescription


@router.post("/", response_model=PrescriptionResponse)
async def create_prescription(
    rx_data: PrescriptionCreate,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new prescription.
    Automatically performs drug interaction and allergy checks.
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == rx_data.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Create prescription via service
    prescription = await PrescriptionService.create_prescription(
        db=db,
        practice_id=current_user.practice_id,
        provider=current_user,
        prescription_data=rx_data.model_dump(exclude_unset=True),
    )

    # Audit log (HIPAA: critical for controlled substances)
    audit_details = {
        "rx_number": prescription.rx_number,
        "medication": prescription.medication_name,
        "patient_id": str(rx_data.patient_id),
        "is_controlled": prescription.is_controlled,
    }
    await log_audit_event(
        db, current_user, "create_prescription", "prescription",
        prescription.id, request, audit_details
    )
    await db.commit()

    return prescription


@router.put("/{prescription_id:uuid}", response_model=PrescriptionResponse)
async def update_prescription(
    prescription_id: UUID,
    rx_data: PrescriptionUpdate,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Update a prescription (only draft/active prescriptions)"""
    result = await db.execute(
        select(Prescription).where(
            Prescription.id == prescription_id,
            Prescription.practice_id == current_user.practice_id,
        )
    )
    prescription = result.scalar_one_or_none()

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    if prescription.status not in [PrescriptionStatus.DRAFT, PrescriptionStatus.ACTIVE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update prescription with status '{prescription.status.value}'",
        )

    update_data = rx_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prescription, field, value)

    # Audit log
    await log_audit_event(
        db, current_user, "update_prescription", "prescription",
        prescription.id, request, update_data
    )

    await db.commit()
    await db.refresh(prescription)

    return prescription


@router.post("/{prescription_id:uuid}/cancel", response_model=PrescriptionResponse)
async def cancel_prescription(
    prescription_id: UUID,
    cancel_data: PrescriptionCancel,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Cancel an active prescription"""
    result = await db.execute(
        select(Prescription).where(
            Prescription.id == prescription_id,
            Prescription.practice_id == current_user.practice_id,
        )
    )
    prescription = result.scalar_one_or_none()

    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    if prescription.status not in [PrescriptionStatus.DRAFT, PrescriptionStatus.ACTIVE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel prescription with status '{prescription.status.value}'",
        )

    prescription = await PrescriptionService.cancel_prescription(
        db, prescription, cancel_data.reason
    )

    # Audit log
    await log_audit_event(
        db, current_user, "cancel_prescription", "prescription",
        prescription.id, request,
        {"reason": cancel_data.reason, "rx_number": prescription.rx_number}
    )
    await db.commit()

    return prescription


@router.get("/patient/{patient_id}")
async def get_patient_prescriptions(
    patient_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get all prescriptions for a patient"""
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    query = select(Prescription).where(
        Prescription.patient_id == patient_id,
        Prescription.practice_id == current_user.practice_id,
    )
    if status_filter:
        query = query.where(Prescription.status == status_filter)

    query = query.order_by(Prescription.prescribed_date.desc())
    result = await db.execute(query)
    prescriptions = result.scalars().all()

    # Audit
    await log_audit_event(
        db, current_user, "view_patient_prescriptions", "prescription", None, request,
        {"patient_id": patient_id}
    )
    await db.commit()

    return {"prescriptions": prescriptions, "count": len(prescriptions)}


# ============================================
# MEDICATION SEARCH ENDPOINTS
# ============================================

@router.get("/medications/search")
async def search_medications(
    q: str = Query(..., min_length=2, description="Search query"),
    source: Optional[str] = Query("all", description="Search source: local, openfda, all"),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Search for medications in local DB and/or OpenFDA"""
    results = {"local": [], "openfda": []}

    if source in ["local", "all"]:
        local_meds = await PrescriptionService.search_medications_local(db, q, limit)
        results["local"] = local_meds

    if source in ["openfda", "all"]:
        openfda_results = await PrescriptionService.search_medications_openfda(q, limit)
        results["openfda"] = openfda_results

    return results


@router.post("/medications/check-interactions", response_model=InteractionCheckResponse)
async def check_interactions(
    check_data: InteractionCheckRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Check drug-drug interactions and allergy conflicts for a patient"""
    interactions, allergy_warnings = await PrescriptionService.check_drug_interactions(
        db, check_data.medication_name, check_data.patient_id
    )

    # Audit log (safety check)
    await log_audit_event(
        db, current_user, "check_drug_interactions", "prescription", None, request,
        {"medication": check_data.medication_name, "patient_id": str(check_data.patient_id)}
    )
    await db.commit()

    return {
        "medication_checked": check_data.medication_name,
        "patient_id": str(check_data.patient_id),
        "has_interactions": len(interactions) > 0,
        "has_allergy_conflicts": len(allergy_warnings) > 0,
        "interactions": interactions,
        "allergy_warnings": allergy_warnings,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/medications/seed")
async def seed_medications(
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Seed common dental medications into the database"""
    count = await PrescriptionService.seed_common_medications(db)
    return {"message": f"Seeded {count} medications", "count": count}


# ============================================
# PATIENT ALLERGY ENDPOINTS
# ============================================

@router.get("/patients/{patient_id}/allergies")
async def get_patient_allergies(
    patient_id: str,
    include_inactive: bool = Query(False, description="Include inactive allergies"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get patient's allergy list"""
    query = select(PatientAllergy).where(
        PatientAllergy.patient_id == patient_id
    )
    if not include_inactive:
        query = query.where(PatientAllergy.is_active == True)

    query = query.order_by(PatientAllergy.severity.desc(), PatientAllergy.allergen)
    result = await db.execute(query)
    allergies = result.scalars().all()

    return {"allergies": allergies, "count": len(allergies)}


@router.post("/patients/{patient_id:uuid}/allergies", response_model=PatientAllergyResponse)
async def add_patient_allergy(
    patient_id: UUID,
    allergy_data: PatientAllergyCreate,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Add an allergy to a patient's record"""
    # Verify patient
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    allergy = PatientAllergy(
        patient_id=patient_id,
        **allergy_data.model_dump()
    )
    db.add(allergy)

    # Audit log (HIPAA: allergy is critical clinical data)
    await log_audit_event(
        db, current_user, "add_patient_allergy", "patient_allergy",
        None, request,
        {"patient_id": patient_id, "allergen": allergy_data.allergen}
    )

    await db.commit()
    await db.refresh(allergy)

    return allergy


@router.put("/patients/{patient_id:uuid}/allergies/{allergy_id:uuid}", response_model=PatientAllergyResponse)
async def update_patient_allergy(
    patient_id: UUID,
    allergy_id: UUID,
    allergy_data: PatientAllergyUpdate,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Update a patient allergy record"""
    result = await db.execute(
        select(PatientAllergy).where(
            PatientAllergy.id == allergy_id,
            PatientAllergy.patient_id == patient_id,
        )
    )
    allergy = result.scalar_one_or_none()

    if not allergy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allergy record not found",
        )

    update_data = allergy_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(allergy, field, value)

    await log_audit_event(
        db, current_user, "update_patient_allergy", "patient_allergy",
        allergy.id, request, update_data
    )

    await db.commit()
    await db.refresh(allergy)

    return allergy


@router.delete("/patients/{patient_id:uuid}/allergies/{allergy_id:uuid}")
async def delete_patient_allergy(
    patient_id: UUID,
    allergy_id: UUID,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Deactivate a patient allergy (soft delete)"""
    result = await db.execute(
        select(PatientAllergy).where(
            PatientAllergy.id == allergy_id,
            PatientAllergy.patient_id == patient_id,
        )
    )
    allergy = result.scalar_one_or_none()

    if not allergy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allergy record not found",
        )

    allergy.is_active = False

    await log_audit_event(
        db, current_user, "deactivate_patient_allergy", "patient_allergy",
        allergy.id, request,
        {"patient_id": patient_id, "allergen": allergy.allergen}
    )

    await db.commit()

    return {"message": "Allergy record deactivated"}


# ============================================
# PATIENT CURRENT MEDICATIONS ENDPOINTS
# ============================================

@router.get("/patients/{patient_id}/medications")
async def get_patient_medications(
    patient_id: str,
    active_only: bool = Query(True, description="Show only active medications"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get patient's current medication list"""
    query = select(PatientMedication).where(
        PatientMedication.patient_id == patient_id
    )
    if active_only:
        query = query.where(PatientMedication.is_active == True)

    query = query.order_by(PatientMedication.medication_name)
    result = await db.execute(query)
    medications = result.scalars().all()

    return {"medications": medications, "count": len(medications)}


@router.post("/patients/{patient_id:uuid}/medications", response_model=PatientMedicationResponse)
async def add_patient_medication(
    patient_id: UUID,
    med_data: PatientMedicationCreate,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Add a medication to patient's current medication list"""
    # Verify patient
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    medication = PatientMedication(
        patient_id=patient_id,
        entered_by=current_user.id,
        **med_data.model_dump()
    )
    db.add(medication)

    await log_audit_event(
        db, current_user, "add_patient_medication", "patient_medication",
        None, request,
        {"patient_id": patient_id, "medication": med_data.medication_name}
    )

    await db.commit()
    await db.refresh(medication)

    return medication


@router.put("/patients/{patient_id:uuid}/medications/{medication_id:uuid}", response_model=PatientMedicationResponse)
async def update_patient_medication(
    patient_id: UUID,
    medication_id: UUID,
    med_data: PatientMedicationUpdate,
    request: Request = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN, UserRole.DENTIST)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Update a patient's current medication"""
    result = await db.execute(
        select(PatientMedication).where(
            PatientMedication.id == medication_id,
            PatientMedication.patient_id == patient_id,
        )
    )
    med = result.scalar_one_or_none()

    if not med:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication record not found",
        )

    update_data = med_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(med, field, value)

    await db.commit()
    await db.refresh(med)

    return med


# ============================================
# PRESCRIPTION TEMPLATE ENDPOINTS
# ============================================

@router.get("/templates/")
async def list_prescription_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search templates"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List prescription templates for the practice"""
    query = select(PrescriptionTemplate).where(
        PrescriptionTemplate.practice_id == current_user.practice_id,
        PrescriptionTemplate.is_active == True,
    )

    if category:
        query = query.where(PrescriptionTemplate.category == category)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            PrescriptionTemplate.name.ilike(search_pattern) |
            PrescriptionTemplate.medication_name.ilike(search_pattern)
        )

    query = query.order_by(PrescriptionTemplate.usage_count.desc(), PrescriptionTemplate.name)
    result = await db.execute(query)
    templates = result.scalars().all()

    return {"templates": templates, "count": len(templates)}


@router.post("/templates/", response_model=PrescriptionTemplateResponse)
async def create_prescription_template(
    template_data: PrescriptionTemplateCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Create a prescription template"""
    template = PrescriptionTemplate(
        practice_id=current_user.practice_id,
        created_by=current_user.id,
        **template_data.model_dump()
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return template


@router.delete("/templates/{template_id:uuid}")
async def delete_prescription_template(
    template_id: UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Deactivate a prescription template"""
    result = await db.execute(
        select(PrescriptionTemplate).where(
            PrescriptionTemplate.id == template_id,
            PrescriptionTemplate.practice_id == current_user.practice_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    template.is_active = False
    await db.commit()

    return {"message": "Template deleted"}
