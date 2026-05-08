"""
Audit Service
Centralized audit logging for HIPAA compliance
"""

from typing import Optional, Any
from uuid import UUID
from datetime import datetime, date, timezone
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.models.user import User


def _make_json_serializable(obj: Any) -> Any:
    """Recursively convert UUIDs, datetimes, and dates to strings for JSON storage."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_serializable(v) for v in obj]
    return obj


class AuditService:
    """Service for audit logging operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        user: Optional[User],
        action: str,
        entity_type: str,
        entity_id: Any,
        request: Optional[Request] = None,
        changes: Optional[dict] = None,
    ) -> AuditLog:
        """
        Log an audit event
        
        Args:
            user: User performing the action
            action: Action being performed (create, read, update, delete)
            entity_type: Type of entity (patient, appointment, etc.)
            entity_id: ID of the entity
            request: FastAPI request object
            changes: Dictionary of changes made
        
        Returns:
            Created audit log entry
        """
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        # Convert entity_id to UUID if it's a string
        if isinstance(entity_id, str):
            try:
                from uuid import uuid5, NAMESPACE_DNS
                entity_id = UUID(entity_id) if len(entity_id) == 36 else uuid5(NAMESPACE_DNS, entity_id)
            except (ValueError, AttributeError):
                from uuid import uuid5, NAMESPACE_DNS
                entity_id = uuid5(NAMESPACE_DNS, str(entity_id))
        
        # Serialize changes for JSON storage
        serialized_changes = _make_json_serializable(changes) if changes is not None else None

        audit_entry = AuditLog(
            user_id=user.id if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=serialized_changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        self.db.add(audit_entry)
        await self.db.flush()
        
        return audit_entry
    
    async def log_phi_access(
        self,
        user: User,
        patient_id: UUID,
        access_type: str,
        request: Optional[Request] = None
    ) -> AuditLog:
        """
        Log PHI (Protected Health Information) access
        
        Args:
            user: User accessing PHI
            patient_id: Patient whose PHI is being accessed
            access_type: Type of access (view, edit, export)
            request: FastAPI request object
        
        Returns:
            Created audit log entry
        """
        return await self.log_event(
            user=user,
            action=f"phi_{access_type}",
            entity_type="patient",
            entity_id=patient_id,
            request=request,
            changes={"access_type": access_type}
        )
