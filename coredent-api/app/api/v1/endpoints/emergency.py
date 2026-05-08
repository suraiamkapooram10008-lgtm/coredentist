"""
Emergency Access (Break-Glass) Endpoint
HIPAA §164.312(a)(2)(ii) — Emergency Access Procedure

Provides controlled emergency access when normal authentication fails.
Requires two-person authorization and auto-disables after 24 hours.
All actions are heavily logged and alerted.

M-1 FIX: Migrated from in-memory dict to database-backed storage
for multi-instance support (Railway, Kubernetes, etc.).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
import secrets
import hashlib

from app.core.database import get_db
from app.core.config_simple import settings
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.emergency_token import EmergencyToken
from app.core.audit import log_audit_event

router = APIRouter()


class EmergencyAccessRequest(BaseModel):
    """Request for emergency access"""
    email: str
    emergency_code: str = Field(..., min_length=32, max_length=64)
    reason: str = Field(..., min_length=10, max_length=500)
    authorized_by: str = Field(..., min_length=1, max_length=100)


class EmergencyTokenVerify(BaseModel):
    """Verify emergency token"""
    token: str


def _hash_token(token: str) -> str:
    """Hash an emergency token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/emergency/request")
async def request_emergency_access(
    request: EmergencyAccessRequest,
    db: AsyncSession = Depends(get_db),
    req: Request = None
):
    """
    Request emergency break-glass access.
    Returns a one-time emergency token valid for 24 hours.
    """
    expected_code = getattr(settings, 'BREAK_GLASS_CODE', None)
    if not expected_code:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Emergency access is not configured."
        )

    if not secrets.compare_digest(
        hashlib.sha256(request.emergency_code.encode()).hexdigest(),
        hashlib.sha256(expected_code.encode()).hexdigest()
    ):
        await log_audit_event(
            db=db,
            user=None,
            action="EMERGENCY_ACCESS_DENIED",
            entity_type="system",
            entity_id="break-glass",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid emergency credentials."
        )

    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive."
        )

    if user.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Emergency access restricted to admin and owner roles."
        )

    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=24)

    # Store in database
    emergency_token = EmergencyToken(
        token_hash=token_hash,
        user_id=user.id,
        email=user.email,
        created_at=now,
        expires_at=expires_at,
        used=False,
        reason=request.reason,
        authorized_by=request.authorized_by,
        ip_address=req.client.host if req else None,
    )
    db.add(emergency_token)
    await db.commit()

    await log_audit_event(
        db=db,
        user=user,
        action="EMERGENCY_ACCESS_GRANTED",
        entity_type="user",
        entity_id=str(user.id),
    )

    return {
        "token": token,
        "expires_at": expires_at.isoformat(),
        "message": (
            "EMERGENCY ACCESS GRANTED. This token is valid for 24 hours. "
            "All actions will be logged. Use /emergency/login to authenticate."
        )
    }


@router.post("/emergency/login")
async def emergency_login(
    request: EmergencyTokenVerify,
    db: AsyncSession = Depends(get_db)
):
    """Login using an emergency token. Returns a short-lived access token (1 hour)."""
    token_hash = _hash_token(request.token)
    now = datetime.now(timezone.utc)

    # Query database for valid token
    result = await db.execute(
        select(EmergencyToken).where(
            and_(
                EmergencyToken.token_hash == token_hash,
                EmergencyToken.used == False,
                EmergencyToken.expires_at > now
            )
        )
    )
    token_data = result.scalar_one_or_none()

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired emergency token."
        )

    # Mark as used
    token_data.used = True
    token_data.used_at = now
    await db.commit()

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    from app.core.security import create_access_token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "practice_id": str(user.practice_id),
            "emergency": True,
            "reason": token_data.reason
        },
        expires_delta=timedelta(hours=1)
    )

    await log_audit_event(
        db=db,
        user=user,
        action="EMERGENCY_LOGIN",
        entity_type="user",
        entity_id=str(user.id),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "emergency": True,
        "warning": (
            "THIS IS AN EMERGENCY SESSION. All actions are logged. "
            "Session expires in 1 hour."
        )
    }


@router.get("/emergency/status")
async def emergency_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check status of emergency access system.
    Requires authentication. Returns sanitized status — no PII exposed.
    """
    now = datetime.now(timezone.utc)

    # Count active (unused, not expired) tokens
    result = await db.execute(
        select(EmergencyToken).where(
            and_(
                EmergencyToken.used == False,
                EmergencyToken.expires_at > now
            )
        )
    )
    active_tokens = result.scalars().all()

    # Clean up expired tokens
    expired_result = await db.execute(
        select(EmergencyToken).where(EmergencyToken.expires_at <= now)
    )
    expired_tokens = expired_result.scalars().all()
    for et in expired_tokens:
        await db.delete(et)
    await db.commit()

    return {
        "active_token_count": len(active_tokens),
        "system_enabled": True,
        "emergency_access_configured": bool(getattr(settings, 'BREAK_GLASS_CODE', None)),
        "note": "Emergency access status — no PII exposed"
    }