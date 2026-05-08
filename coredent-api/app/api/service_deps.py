"""
Service Dependencies
Dependency injection for service layer
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.patient_service import PatientService
from app.services.appointment_service import AppointmentService
from app.services.billing_service import BillingService
from app.services.insurance_service import InsuranceService
from app.services.audit_service import AuditService


async def get_audit_service(
    db: AsyncSession = Depends(get_db)
) -> AuditService:
    """Get audit service instance"""
    return AuditService(db)


async def get_patient_service(
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service)
) -> PatientService:
    """Get patient service instance"""
    return PatientService(db, audit_service)


async def get_appointment_service(
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service)
) -> AppointmentService:
    """Get appointment service instance"""
    return AppointmentService(db, audit_service)


async def get_billing_service(
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service)
) -> BillingService:
    """Get billing service instance"""
    return BillingService(db, audit_service)


async def get_insurance_service(
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service)
) -> InsuranceService:
    """Get insurance service instance"""
    return InsuranceService(db, audit_service)
