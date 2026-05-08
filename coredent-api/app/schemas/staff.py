"""
Staff Management Schemas
Pydantic models for staff create/update — prevents arbitrary field writes via setattr
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from app.models.user import UserRole


class StaffCreate(BaseModel):
    """Schema for creating a staff member — allowlist of permitted fields"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.FRONT_DESK
    password: str = Field("CoreDent123!", min_length=8)


class StaffUpdate(BaseModel):
    """Schema for updating a staff member — only allowed fields can be set"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=8)
