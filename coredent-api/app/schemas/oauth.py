"""
OAuth Authentication Schemas
Google OAuth and Apple Sign-In
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class OAuthLoginRequest(BaseModel):
    """OAuth login request — receives ID token from client"""
    id_token: str
    provider: str  # "google" or "apple"


class OAuthUserResponse(BaseModel):
    """OAuth user data extracted from ID token"""
    provider: str
    provider_user_id: str
    email: EmailStr
    first_name: str
    last_name: str
    picture: Optional[str] = None


class OAuthLoginResponse(BaseModel):
    """OAuth login response — same shape as LoginResponse"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    csrf_token: str
    is_new_user: bool = False