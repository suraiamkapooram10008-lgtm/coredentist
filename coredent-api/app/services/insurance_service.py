"""
Insurance Service
Business logic for insurance claims and eligibility
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.insurance import InsuranceClaim, Eligibility
from app.models.user import User
from app.schemas.insurance import InsuranceClaimCreate
from app.services.base_service import BaseService
from app.services.audit_service import AuditService


class InsuranceService(BaseService[InsuranceClaim]):
    """Service for insurance operations"""
    
    def __init__(self, db: AsyncSession, audit_service: AuditService):
        super().__init__(db, InsuranceClaim)
        self.audit_service = audit_service
    
    async def create_claim(
        self,
        claim_data: InsuranceClaimCreate,
        user: User,
        request: Optional[Request] = None
    ) -> InsuranceClaim:
        """
        Create a new insurance claim
        
        Args:
            claim_data: Claim creation data
            user: User creating the claim
            request: FastAPI request object
        
        Returns:
            Created claim
        """
        # Generate claim number
        claim_number = await self._generate_claim_number()
        
        # Create claim
        claim = InsuranceClaim(
            **claim_data.model_dump(),
            claim_number=claim_number,
            status="draft"
        )
        
        claim = await self.create(claim)
        
        # Audit log
        await self.audit_service.log_event(
            user=user,
            action="create",
            entity_type="insurance_claim",
            entity_id=claim.id,
            request=request,
            changes=claim_data.model_dump()
        )
        
        return claim
    
    async def submit_claim(
        self,
        claim_id: UUID,
        user: User,
        request: Optional[Request] = None
    ) -> InsuranceClaim:
        """
        Submit a claim to insurance
        
        Args:
            claim_id: Claim ID
            user: User submitting the claim
            request: FastAPI request object
        
        Returns:
            Updated claim
        """
        claim = await self.get_by_id(claim_id)
        
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found"
            )
        
        if claim.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft claims can be submitted"
            )
        
        # Update claim status
        claim.status = "submitted"
        claim.submitted_at = datetime.utcnow()
        claim.updated_at = datetime.utcnow()
        
        claim = await self.update(claim)
        
        # Audit log
        await self.audit_service.log_event(
            user=user,
            action="submit",
            entity_type="insurance_claim",
            entity_id=claim.id,
            request=request,
            changes={"status": "submitted"}
        )
        
        # TODO: Integrate with EDI system to actually submit claim
        
        return claim
    
    async def check_eligibility(
        self,
        patient_id: UUID,
        insurance_id: UUID,
        user: User,
        request: Optional[Request] = None
    ) -> Eligibility:
        """
        Check insurance eligibility for a patient
        
        Args:
            patient_id: Patient ID
            insurance_id: Insurance ID
            user: User checking eligibility
            request: FastAPI request object
        
        Returns:
            Eligibility check result
        """
        # Check for recent eligibility check (within 24 hours)
        from datetime import timedelta
        recent_check = await self._get_recent_eligibility(patient_id, insurance_id)
        
        if recent_check:
            return recent_check
        
        # TODO: Integrate with real-time eligibility API
        # For now, create a placeholder
        eligibility = Eligibility(
            patient_id=patient_id,
            insurance_id=insurance_id,
            status="pending",
            checked_at=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.db.add(eligibility)
        await self.db.flush()
        
        # Audit log
        await self.audit_service.log_event(
            user=user,
            action="check_eligibility",
            entity_type="eligibility",
            entity_id=eligibility.id,
            request=request,
            changes={"patient_id": str(patient_id), "insurance_id": str(insurance_id)}
        )
        
        return eligibility
    
    async def _generate_claim_number(self) -> str:
        """Generate unique claim number"""
        from sqlalchemy import func
        
        # Get count of claims today
        today = datetime.utcnow().date()
        result = await self.db.execute(
            select(func.count()).select_from(InsuranceClaim).where(
                func.date(InsuranceClaim.created_at) == today
            )
        )
        count = result.scalar_one()
        
        # Format: CLM-YYYYMMDD-NNNN
        return f"CLM-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    
    async def _get_recent_eligibility(
        self,
        patient_id: UUID,
        insurance_id: UUID
    ) -> Optional[Eligibility]:
        """Get recent eligibility check if available"""
        result = await self.db.execute(
            select(Eligibility).where(
                Eligibility.patient_id == patient_id,
                Eligibility.insurance_id == insurance_id,
                Eligibility.valid_until > datetime.utcnow()
            ).order_by(Eligibility.checked_at.desc())
        )
        return result.scalar_one_or_none()
