"""
Audit Logging Utilities
Functions for HIPAA-compliant audit events
"""

from typing import Any, Optional
import inspect
import asyncio
from uuid import UUID
from datetime import datetime, date, timezone
from decimal import Decimal
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.models.user import User


def _make_json_serializable(obj: Any) -> Any:
    """Recursively convert UUIDs, datetimes, Decimals, and dates to strings for JSON storage."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_serializable(v) for v in obj]
    return obj


async def log_audit_event(
    db: AsyncSession,
    user: Optional[User],
    action: str,
    entity_type: str,
    entity_id: Any,  # Changed from UUID to Any to accept strings
    request: Optional[Request] = None,
    changes: Optional[dict] = None,
) -> None:
    """
    Log an audit event to the database
    
    Supports both AsyncSession and sync Session objects.
    """
    ip_address = None
    user_agent = None
    
    if request:
        from app.core.request_utils import get_client_ip
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("user-agent")
    
    # For SQLite compatibility: convert entity_id to UUID
    if isinstance(entity_id, str):
        try:
            # Try to parse as UUID
            entity_id = UUID(entity_id)
        except (ValueError, AttributeError):
            # Not a valid UUID, create one from the string
            from uuid import uuid5, NAMESPACE_DNS
            entity_id = uuid5(NAMESPACE_DNS, entity_id)
        except TypeError:
            # entity_id is None or other non-string
            pass
    
    serialized_changes = _make_json_serializable(changes) if changes is not None else None

    audit_entry = AuditLog(
        user_id=user.id if user else None,  # Keep as UUID object
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=serialized_changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    db.add(audit_entry)
    # Support both async and sync sessions
    if asyncio.iscoroutinefunction(db.flush):
        # It's an async session
        await db.flush()
    else:
        # It's a sync session
        db.flush()
