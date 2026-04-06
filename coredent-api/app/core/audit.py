"""
Audit Logging Utilities
Functions for logging HIPAA-compliant audit events
"""

from typing import Any, Optional
from uuid import UUID
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.models.user import User

async def log_audit_event(
    db: AsyncSession,
    user: Optional[User],
    action: str,
    entity_type: str,
    entity_id: UUID,
    request: Optional[Request] = None,
    changes: Optional[dict] = None,
) -> None:
    """
    Log an audit event to the database
    """
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
    audit_entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    db.add(audit_entry)
    # We use await db.flush() instead of commit() to allow the caller to handle the transaction
    await db.flush()
