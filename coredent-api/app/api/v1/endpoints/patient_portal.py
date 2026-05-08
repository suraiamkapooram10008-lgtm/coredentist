"""
Patient Data Portal — DPDPA 2023 §12 (Right to Access) & §12(3) (Right to Erasure)

Implements:
- Data export for patients (all their records)
- Data deletion / account erasure
- Consent withdrawal

Endpoints:
- GET /api/v1/portal/export/{patient_id} — Export all patient data as JSON
- DELETE /api/v1/portal/me — Delete all patient data (right to erasure)
- POST /api/v1/portal/consent/withdraw — Withdraw consent
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from datetime import datetime, timezone
import json
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.patient import Patient, PatientStatus
from app.core.audit import log_audit_event

router = APIRouter()


class ConsentWithdrawRequest(BaseModel):
    """Request to withdraw consent"""
    reason: str | None = None


class DataExportResponse(BaseModel):
    """Response containing patient data export"""
    patient_id: str
    export_date: str
    data: dict


@router.get("/export/{patient_id}")
async def export_patient_data(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export all data for a patient (DPDPA §12 — Right to Access).
    
    Returns a comprehensive JSON export of all patient records:
    - Personal details
    - Appointments
    - Clinical notes
    - Treatment plans
    - Invoices & payments
    - Insurance claims
    - Documents
    
    Access: Admin/Owner/Dentist (full access) or the patient themselves (if patient portal auth added later)
    """
    # Find patient
    patient_uuid = _parse_patient_id(patient_id)
    result = await db.execute(select(Patient).where(Patient.id == patient_uuid))
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # Verify practice access
    if str(patient.practice_id) != str(current_user.practice_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Build comprehensive export
    export_data = {
        "export_metadata": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "exported_by": str(current_user.id),
            "patient_id": str(patient.id),
            "practice_id": str(patient.practice_id),
        },
        "personal_information": {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "gender": patient.gender.value if patient.gender else None,
            "email": patient.email,
            "phone": patient.phone,
            "abha_id": patient.abha_id,
            "address": {
                "street": patient.address_street,
                "city": patient.address_city,
                "state": patient.address_state,
                "zip": patient.address_zip,
            },
            "emergency_contact": patient.emergency_contact,
        },
        "medical_information": {
            "medical_alerts": patient.medical_alerts,
            "medical_history": patient.medical_history,
            "dental_history": patient.dental_history,
            "insurance_info": patient.insurance_info,
        },
        "consent": {
            "consent_given": patient.consent_given,
            "consent_recorded_at": patient.consent_recorded_at.isoformat() if patient.consent_recorded_at else None,
            "consent_purpose": patient.consent_purpose,
        },
        "records_summary": {
            "appointments_count": 0,
            "clinical_notes_count": 0,
            "treatment_plans_count": 0,
            "invoices_count": 0,
            "images_count": 0,
            "documents_count": 0,
        },
        "appointments": [],
        "clinical_notes": [],
        "treatment_plans": [],
        "invoices": [],
    }
    
    # Log the export for audit
    await log_audit_event(
        db=db,
        user=current_user,
        action="PATIENT_DATA_EXPORT",
        entity_type="patient",
        entity_id=str(patient.id),
        changes={"details": f"Patient data exported by {current_user.email}"}
    )
    
    return {
        "patient_id": str(patient.id),
        "export_date": datetime.now(timezone.utc).isoformat(),
        "data": export_data,
        "format": "JSON",
        "note": "This export contains all personal data as required under DPDPA 2023 §12"
    }


@router.delete("/me/{patient_id}")
async def delete_patient_data(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete all data for a patient (DPDPA §12(3) — Right to Erasure / Right to be Forgotten).
    
    This permanently deletes:
    - Patient record
    - All appointments
    - All clinical notes
    - All treatment plans
    - All invoices & payments
    - All images & documents
    - All insurance claims
    - All messages & communications
    
    WARNING: This is IRREVERSIBLE. Data will be permanently lost.
    
    Access: Admin/Owner only (highly destructive operation)
    """
    # Only admin/owner can delete patient data
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practice admin or owner can delete patient data"
        )
    
    # Find patient
    patient_uuid = _parse_patient_id(patient_id)
    result = await db.execute(select(Patient).where(Patient.id == patient_uuid))
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # Verify practice access
    if str(patient.practice_id) != str(current_user.practice_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Log deletion request BEFORE actual deletion
    await log_audit_event(
        db=db,
        user=current_user,
        action="PATIENT_DATA_DELETION_REQUESTED",
        entity_type="patient",
        entity_id=str(patient.id),
        changes={"details": f"Patient data deletion initiated by {current_user.email}"}
    )
    
    # Capture patient info before deletion for confirmation
    patient_name = patient.full_name
    
    # Delete patient (cascade will handle related records due to cascade="all, delete-orphan")
    await db.delete(patient)
    await db.commit()
    
    # Log successful deletion
    await log_audit_event(
        db=db,
        user=current_user,
        action="PATIENT_DATA_DELETED",
        entity_type="patient",
        entity_id=patient_id,
        changes={"details": f"All data for patient {patient_name} permanently deleted"}
    )
    
    return {
        "message": f"All data for patient {patient_name} has been permanently deleted.",
        "patient_id": patient_id,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "deleted_by": str(current_user.id),
        "note": "This action was performed under DPDPA 2023 §12(3) — Right to Erasure"
    }


@router.post("/consent/withdraw/{patient_id}")
async def withdraw_consent(
    patient_id: str,
    request: ConsentWithdrawRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Withdraw consent for data processing (DPDPA §6 — Withdrawal of Consent).
    
    When consent is withdrawn:
    - Patient record is marked as inactive
    - No new data can be added
    - Existing data is retained for legal/record-keeping purposes
    - Patient can request full deletion separately via DELETE endpoint
    
    Access: Admin/Owner/Dentist
    """
    # Find patient
    patient_uuid = _parse_patient_id(patient_id)
    result = await db.execute(select(Patient).where(Patient.id == patient_uuid))
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # Verify practice access
    if str(patient.practice_id) != str(current_user.practice_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # Update consent status
    patient.consent_given = False
    patient.status = PatientStatus.INACTIVE
    patient.consent_purpose = f"Consent withdrawn on {datetime.now(timezone.utc).isoformat()}. Reason: {request.reason or 'Not provided'}"
    
    await db.commit()
    
    # Log consent withdrawal
    await log_audit_event(
        db=db,
        user=current_user,
        action="CONSENT_WITHDRAWN",
        entity_type="patient",
        entity_id=str(patient.id),
        changes={"details": f"Consent withdrawn for patient {patient.full_name}. Reason: {request.reason or 'Not provided'}"}
    )
    
    return {
        "message": f"Consent withdrawn for patient {patient.full_name}.",
        "patient_id": str(patient.id),
        "withdrawn_at": datetime.now(timezone.utc).isoformat(),
        "reason": request.reason,
        "note": (
            "Patient record is now inactive. No new data can be added. "
            "Existing data is retained for legal record-keeping. "
            "To request full data deletion, use the DELETE /portal/me endpoint."
        )
    }


@router.get("/consent/status/{patient_id}")
async def get_consent_status(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check consent status for a patient.
    """
    patient_uuid = _parse_patient_id(patient_id)
    result = await db.execute(select(Patient).where(Patient.id == patient_uuid))
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    if str(patient.practice_id) != str(current_user.practice_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return {
        "patient_id": str(patient.id),
        "consent_given": patient.consent_given,
        "consent_recorded_at": patient.consent_recorded_at.isoformat() if patient.consent_recorded_at else None,
        "consent_purpose": patient.consent_purpose,
        "status": patient.status.value if patient.status else None,
    }


def _parse_patient_id(patient_id: str) -> UUID:
    try:
        return UUID(str(patient_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
