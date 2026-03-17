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
    """Token payload data"""
    sub: str  # user_id
    email: str
    role: UserRole
    practice_id: UUID
    type: str  # "access" or "refresh"


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
