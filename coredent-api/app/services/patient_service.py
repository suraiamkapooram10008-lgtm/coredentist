"""
Patient Service
Business logic for patient management
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException, status, Request
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.base_service import BaseService
from app.services.audit_service import AuditService


class PatientService(BaseService[Patient]):
    """Service for patient operations"""
    
    def __init__(self, db: AsyncSession, audit_service: AuditService):
        super().__init__(db, Patient)
        self.audit_service = audit_service
    
    async def create_patient(
        self,
        patient_data: PatientCreate,
        user: User,
        request: Optional[Request] = None
    ) -> Patient:
        """
        Create a new patient with validation and audit logging
        
        Args:
            patient_data: Patient creation data
            user: User creating the patient
            request: FastAPI request object
        
        Returns:
            Created patient
        
        Raises:
            HTTPException: If validation fails
        """
        # Validate practice access
        if patient_data.practice_id != user.practice_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create patient for different practice"
            )
        
        # Check for duplicate email in practice
        if patient_data.email:
            existing = await self._find_by_email(
                patient_data.email,
                patient_data.practice_id
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Patient with this email already exists"
                )
        
        # Create patient
        patient = Patient(**patient_data.model_dump())
        patient = await self.create(patient)
        
        # Audit log
        await self.audit_service.log_event(
            user=user,
            action="create",
            entity_type="patient",
            entity_id=patient.id,
            request=request,
            changes=patient_data.model_dump()
        )
        
        return patient
    
    async def update_patient(
        self,
        patient_id: UUID,
        patient_data: PatientUpdate,
        user: User,
        request: Optional[Request] = None
    ) -> Patient:
        """
        Update patient with validation and audit logging
        
        Args:
            patient_id: Patient ID
            patient_data: Patient update data
            user: User updating the patient
            request: FastAPI request object
        
        Returns:
            Updated patient
        
        Raises:
            HTTPException: If patient not found or validation fails
        """
        patient = await self.get_by_id(patient_id)
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Validate practice access
        if patient.practice_id != user.practice_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access patient from different practice"
            )
        
        # Track changes for audit
        changes = {}
        update_data = patient_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            old_value = getattr(patient, field)
            if old_value != value:
                changes[field] = {"old": old_value, "new": value}
                setattr(patient, field, value)
        
        patient.updated_at = datetime.utcnow()
        patient = await self.update(patient)
        
        # Audit log
        if changes:
            await self.audit_service.log_event(
                user=user,
                action="update",
                entity_type="patient",
                entity_id=patient.id,
                request=request,
                changes=changes
            )
        
        return patient
    
    async def get_patient(
        self,
        patient_id: UUID,
        user: User,
        request: Optional[Request] = None
    ) -> Patient:
        """
        Get patient with access control and audit logging
        
        Args:
            patient_id: Patient ID
            user: User accessing the patient
            request: FastAPI request object
        
        Returns:
            Patient
        
        Raises:
            HTTPException: If patient not found or access denied
        """
        patient = await self.get_by_id(patient_id)
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Validate practice access
        if patient.practice_id != user.practice_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access patient from different practice"
            )
        
        # Log PHI access
        await self.audit_service.log_phi_access(
            user=user,
            patient_id=patient.id,
            access_type="view",
            request=request
        )
        
        return patient
    
    async def search_patients(
        self,
        practice_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Patient]:
        """
        Search patients by name, email, or phone
        
        Args:
            practice_id: Practice ID
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of matching patients
        """
        search_query = select(Patient).where(
            Patient.practice_id == practice_id,
            or_(
                Patient.first_name.ilike(f"%{query}%"),
                Patient.last_name.ilike(f"%{query}%"),
                Patient.email.ilike(f"%{query}%"),
                Patient.phone.ilike(f"%{query}%")
            )
        ).offset(skip).limit(limit)
        
        result = await self.db.execute(search_query)
        return list(result.scalars().all())
    
    async def get_practice_patients(
        self,
        practice_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> tuple[List[Patient], int]:
        """
        Get all patients for a practice with pagination
        
        Args:
            practice_id: Practice ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
        
        Returns:
            Tuple of (patients list, total count)
        """
        filters = {"practice_id": practice_id}
        if status:
            filters["status"] = status
        
        patients = await self.get_all(skip=skip, limit=limit, filters=filters)
        total = await self.count(filters=filters)
        
        return patients, total
    
    async def _find_by_email(
        self,
        email: str,
        practice_id: UUID
    ) -> Optional[Patient]:
        """Find patient by email within practice"""
        result = await self.db.execute(
            select(Patient).where(
                Patient.email == email,
                Patient.practice_id == practice_id
            )
        )
        return result.scalar_one_or_none()
