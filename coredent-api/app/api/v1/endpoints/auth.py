"""
Authentication Endpoints
Login, logout, token refresh, password reset
"""

import inspect

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_password_strength,
)
from app.core.config import settings
from app.core.email import email_service
from app.models.user import User
from app.models.audit import Session as UserSession
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenResponse,
    TokenRefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.user import UserResponse
from app.api.deps import get_current_user, verify_csrf
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


async def _await_if_needed(value: Any) -> Any:
    """Await if the value is awaitable (supports sync+async sessions)."""
    if inspect.isawaitable(value):
        return await value
    return value

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")  # SECURITY FIX: Only 5 login attempts per minute
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
    # NOTE: CSRF is NOT required on login because user doesn't have a session yet.
    # CSRF protection applies to state-changing endpoints AFTER authentication.
) -> Any:
    """
    Login with email and password
    Returns access and refresh tokens
    """
    # Find user by email
    result = await _await_if_needed(db.execute(select(User).where(User.email == credentials.email)))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "practice_id": str(user.practice_id),
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Update last login
    await _await_if_needed(
        db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login=datetime.now(timezone.utc))
        )
    )
    
    # Store refresh token in database
    session = UserSession(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(session)

    await _await_if_needed(db.commit())

    # Set CSRF cookie for client-side protection
    from fastapi.responses import JSONResponse
    from app.core.security import generate_csrf_token
    csrf_token = generate_csrf_token()
    
    # CRIT-01/CRIT-03 FIX: Use Bearer token auth strategy for cross-origin deployment.
    # httpOnly cookies don't work cross-origin unless domains share a parent domain.
    # For Railway deployment with separate frontend/backend domains, use Authorization header.
    # Tokens are returned in response body - frontend stores in memory (NOT localStorage).
    response = JSONResponse(content={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "csrf_token": csrf_token,
        "message": "Login successful",
    })
    
    # Set CSRF cookie (httpOnly for security, Lax SameSite for cross-origin safety)
    # CRIT-03 FIX: Changed samesite from "none" to "lax" to prevent CSRF attacks
    # while still allowing safe cross-origin navigation
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        secure=True,
        samesite="lax",    # FIX: Prevent CSRF - only sent on safe cross-origin requests
        max_age=86400,  # 24 hours
        path="/"
    )
    
    return response


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Logout and invalidate refresh token
    CRIT-01 FIX: Uses Authorization header for auth, no cookie cleanup needed
    """
    # Try to get refresh_token from request body
    body = await request.body()
    try:
        import json
        body_data = json.loads(body) if body else {}
        refresh_token = body_data.get("refresh_token")
    except json.JSONDecodeError:
        refresh_token = None
    
    # Delete session if refresh token provided
    if refresh_token:
        result = await _await_if_needed(
            db.execute(
                select(UserSession).where(
                    UserSession.user_id == current_user.id,
                    UserSession.refresh_token == refresh_token,
                )
            )
        )
        session = result.scalar_one_or_none()
        
        if session:
            await _await_if_needed(db.delete(session))
            await _await_if_needed(db.commit())
    
    # Clear CSRF cookie only (no token cookies to clear with Bearer auth)
    from fastapi.responses import JSONResponse
    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie(key="csrf_token", path="/")
    
    return response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_in: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),  # SECURITY FIX: Verify CSRF token
) -> Any:
    """
    Refresh access token using refresh token
    """
    # Decode refresh token
    payload = decode_token(refresh_in.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Check if session exists
    result = await _await_if_needed(
        db.execute(
            select(UserSession).where(UserSession.refresh_token == refresh_in.refresh_token)
        )
    )
    session = result.scalar_one_or_none()
    
    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or invalid",
        )
    
    # Get user
    result = await _await_if_needed(db.execute(select(User).where(User.id == session.user_id)))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Create new tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "practice_id": str(user.practice_id),
    }
    
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    # Update session with new refresh token
    session.refresh_token = new_refresh_token
    session.expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await _await_if_needed(db.commit())
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user information
    """
    return current_user


@router.post("/forgot-password")
@limiter.limit("5/minute")  # SECURITY: Prevent email enumeration/brute force
async def forgot_password(
    request: Request,
    forgot_in: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Request password reset
    Sends email with reset token
    """
    # Find user
    result = await _await_if_needed(db.execute(select(User).where(User.email == forgot_in.email)))
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    from app.core.security import generate_password_reset_token
    reset_token = generate_password_reset_token()
    
    # Store reset token in user record (with expiration)
    from datetime import datetime, timedelta
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiration
    
    await _await_if_needed(db.commit())
    
    # Send password reset email
    try:
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        await email_service.send_email(
            to=user.email,
            subject="Password Reset - CoreDent",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Password Reset Request</h1>
                    <p>You requested a password reset. Click the link below to reset your password:</p>
                    <p><a href="{reset_link}" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Reset Password</a></p>
                    <p>Or copy this link: {reset_link}</p>
                    <p>This link expires in 24 hours.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">CoreDent Dental Practice Management</p>
                </body>
            </html>
            """,
            text_content=f"Reset your password: {reset_link}. This link expires in 24 hours."
        )
    except Exception as e:
        import logging
        logging.warning(f"Failed to send password reset email: {e}")
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
@limiter.limit("5/minute")  # SECURITY: Prevent brute force
async def reset_password(
    request: Request,
    reset_in: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Reset password with token
    """
    # Validate reset token
    from datetime import datetime
    
    result = await _await_if_needed(
        db.execute(
            select(User).where(
                User.password_reset_token == reset_in.token,
                User.password_reset_expires > datetime.utcnow()
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(reset_in.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )
    
    # Update user password
    user.password_hash = get_password_hash(reset_in.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.password_changed_at = datetime.utcnow()
    
    await _await_if_needed(db.commit())
    
    return {"message": "Password reset successful"}
