"""
MFA / TOTP Endpoints
HIPAA §164.312(a)(2)(ii) — Person or Entity Authentication
Implements TOTP-based multi-factor authentication
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field
from typing import Optional
import pyotp
import json
import secrets
import hashlib

from app.core.database import get_db
from app.api.deps import get_current_user
from app.core.config_simple import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_csrf_token,
    hash_token,
)
from app.models.audit import Session as UserSession
from app.models.user import User
from app.core.audit import log_audit_event

router = APIRouter()


class MFAToggleRequest(BaseModel):
    """Request to enable/disable MFA"""
    enabled: bool
    totp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class TOTPVerifyRequest(BaseModel):
    """Request to verify TOTP during login"""
    mfa_token: str = Field(..., description="Temporary token from password login")
    totp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    backup_code: Optional[str] = Field(None, min_length=8, max_length=8)


class MFASetupResponse(BaseModel):
    """Response with MFA setup details"""
    secret: str
    qr_uri: str
    backup_codes: list[str]
    message: str


def _hash_backup_code(code: str) -> str:
    """Hash a backup code for storage (not plaintext)"""
    return hashlib.sha256(code.encode()).hexdigest()[:32]


def _generate_backup_codes(count: int = 8) -> list[str]:
    """Generate random backup codes for MFA recovery"""
    return [secrets.token_hex(4).upper() for _ in range(count)]


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate MFA secret and backup codes for the current user.
    Returns TOTP secret and QR code URI for authenticator apps.
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled. Disable it first to regenerate."
        )

    # Generate new TOTP secret
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    
    # Build QR URI for authenticator apps
    issuer_name = "CoreDent"
    account_name = current_user.email
    qr_uri = totp.provisioning_uri(name=account_name, issuer_name=issuer_name)
    
    # Generate backup codes
    backup_codes = _generate_backup_codes()
    hashed_codes = [_hash_backup_code(c) for c in backup_codes]
    
    # Store secret and hashed backup codes (not enabled until verified)
    current_user.mfa_secret = secret
    current_user.mfa_backup_codes = json.dumps(hashed_codes)
    current_user.mfa_verified = False
    await db.commit()
    
    # Log MFA setup initiated
    await log_audit_event(
        db=db,
        user=current_user,
        action="MFA_SETUP_INITIATED",
        entity_type="user",
        entity_id=str(current_user.id),
    )
    
    return MFASetupResponse(
        secret=secret,
        qr_uri=qr_uri,
        backup_codes=backup_codes,
        message="Scan the QR code with your authenticator app, then verify with a code to enable MFA."
    )


@router.post("/verify-setup")
async def verify_mfa_setup(
    request: MFAToggleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify TOTP code and enable MFA for the current user.
    """
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not initiated. Call /setup first."
        )
    
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled."
        )
    
    # Verify TOTP code
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(request.totp_code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code. Please try again."
        )
    
    # Enable MFA
    current_user.mfa_enabled = True
    current_user.mfa_verified = True
    await db.commit()
    
    # Log MFA enabled
    await log_audit_event(
        db=db,
        user=current_user,
        action="MFA_ENABLED",
        entity_type="user",
        entity_id=str(current_user.id),
    )
    
    return {"message": "MFA enabled successfully. Save your backup codes securely."}


@router.post("/disable")
async def disable_mfa(
    request: MFAToggleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable MFA for the current user after TOTP verification.
    """
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled."
        )
    
    # Verify TOTP code before disabling
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(request.totp_code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code. MFA cannot be disabled without verification."
        )
    
    # Disable MFA
    current_user.mfa_enabled = False
    current_user.mfa_verified = False
    current_user.mfa_secret = None
    current_user.mfa_backup_codes = None
    await db.commit()
    
    # Log MFA disabled
    await log_audit_event(
        db=db,
        user=current_user,
        action="MFA_DISABLED",
        entity_type="user",
        entity_id=str(current_user.id),
    )
    
    return {"message": "MFA disabled successfully."}


@router.post("/verify")
async def verify_mfa_login(
    http_request: Request,
    request: TOTPVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify TOTP code during login flow.
    Called after successful password authentication.
    
    CRIT-13 FIX: Requires a valid mfa_token to prevent password bypass.
    """
    # 1. Verify the MFA session token
    payload = decode_token(request.mfa_token)
    if not payload or payload.get("type") != "mfa_session" or not payload.get("mfa_pending"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA session. Please log in again."
        )
    
    user_id = payload.get("sub")
    
    # 2. Find user from token
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not enabled or user not found."
        )
    
    # 3. Verify TOTP code
    totp = pyotp.TOTP(user.mfa_secret)
    if totp.verify(request.totp_code, valid_window=1):
        # Success — generate full auth tokens and cookies
        token_data = {
            "sub": str(user.id),
            "role": user.role.value,
            "practice_id": str(user.practice_id),
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        csrf_token = generate_csrf_token()

        session = UserSession(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=http_request.headers.get("X-Forwarded-For", http_request.client.host if http_request.client else None),
            user_agent=http_request.headers.get("user-agent"),
        )
        db.add(session)
        await db.commit()
        
        await log_audit_event(
            db=db,
            user=user,
            action="MFA_VERIFIED",
            entity_type="user",
            entity_id=str(user.id),
        )

        response = JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "csrf_token": csrf_token,
                "mfa_verified": True,
            }
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/api/v1/auth/refresh",
        )
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=86400,
            path="/",
        )
        return response
    
    # Try backup code if provided
    if request.backup_code:
        hashed_input = _hash_backup_code(request.backup_code.upper())
        stored_codes = json.loads(user.mfa_backup_codes or "[]")
        if hashed_input in stored_codes:
            # Remove used backup code
            stored_codes.remove(hashed_input)
            user.mfa_backup_codes = json.dumps(stored_codes)
            await db.commit()
            
            token_data = {
                "sub": str(user.id),
                "role": user.role.value,
                "practice_id": str(user.practice_id),
            }
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            csrf_token = generate_csrf_token()

            session = UserSession(
                user_id=user.id,
                token_hash=hash_token(refresh_token),
                expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                ip_address=http_request.headers.get("X-Forwarded-For", http_request.client.host if http_request.client else None),
                user_agent=http_request.headers.get("user-agent"),
            )
            db.add(session)
            await db.commit()
            
            await log_audit_event(
                db=db,
                user=user,
                action="MFA_BACKUP_CODE_USED",
                entity_type="user",
                entity_id=str(user.id),
            )

            response = JSONResponse(content={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "csrf_token": csrf_token,
                "mfa_verified": True,
                "warning": "Backup code used. Generate new backup codes in settings."
            })
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
                path="/api/v1/auth/refresh",
            )
            response.set_cookie(
                key="csrf_token",
                value=csrf_token,
                httponly=False,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                max_age=86400,
                path="/",
            )
            return response
    
    # Failed verification
    await log_audit_event(
        db=db,
        user=user,
        action="MFA_VERIFICATION_FAILED",
        entity_type="user",
        entity_id=str(user.id),
    )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid TOTP code or backup code."
    )


@router.get("/status")
async def get_mfa_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get current MFA status for the authenticated user.
    """
    return {
        "mfa_enabled": current_user.mfa_enabled,
        "mfa_verified": current_user.mfa_verified,
        "backup_codes_remaining": len(json.loads(current_user.mfa_backup_codes or "[]")) if current_user.mfa_backup_codes else 0
    }
