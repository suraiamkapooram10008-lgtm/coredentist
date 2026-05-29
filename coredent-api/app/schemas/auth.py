"""
Authentication Schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Self-serve practice registration request.

    Creates a new Practice (tenant) and its first OWNER user atomically.
    """
    practice_name: str = Field(..., min_length=2, max_length=255)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=12)
    country: str = Field(default="US", min_length=2, max_length=2)
    phone: Optional[str] = Field(default=None, max_length=20)


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginResponse(TokenResponse):
    """Login response schema"""
    csrf_token: str


class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class TokenData(BaseModel):
    """Token payload data (Hardened: No PHI)"""
    sub: str  # user_id
    role: UserRole
    practice_id: UUID
    type: str  # "access" or "refresh"
    email: Optional[str] = None # No longer stored in JWT


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    token: str
    new_password: str = Field(..., min_length=8)


class InvitationValidateResponse(BaseModel):
    """Invitation validation response"""
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    practice_name: str


class AcceptInvitationRequest(BaseModel):
    """Accept invitation request"""
    token: str
    password: str = Field(..., min_length=8)
