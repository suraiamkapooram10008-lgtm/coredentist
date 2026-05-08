"""
Referral Schemas
Pydantic models for referral management
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.models.referral import ReferralStatus, ReferralType, ReferralSource

class ReferralSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_type: ReferralSource
    contact_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)
    specialty: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    is_track_referrals: bool = True
    notes: Optional[str] = None

class ReferralSourceCreate(ReferralSourceBase):
    pass

class ReferralSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    source_type: Optional[ReferralSource] = None
    contact_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)
    specialty: Optional[str] = Field(None, max_length=100)
    license_number: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    is_track_referrals: Optional[bool] = None
    notes: Optional[str] = None

class ReferralSourceResponse(ReferralSourceBase):
    id: UUID
    practice_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ReferralBase(BaseModel):
    patient_id: UUID
    referral_source_id: Optional[UUID] = None
    referral_type: ReferralType
    status: ReferralStatus = ReferralStatus.PENDING
    reason: str
    clinical_notes: Optional[str] = None
    specialist_name: Optional[str] = Field(None, max_length=255)
    specialist_address: Optional[str] = Field(None, max_length=255)
    specialist_phone: Optional[str] = Field(None, max_length=20)
    specialist_fax: Optional[str] = Field(None, max_length=20)
    appointment_date: Optional[datetime] = None
    referral_fee: Optional[Decimal] = None
    is_urgent: bool = False
    urgent_reason: Optional[str] = None

class ReferralCreate(ReferralBase):
    pass

class ReferralUpdate(BaseModel):
    referral_source_id: Optional[UUID] = None
    referral_type: Optional[ReferralType] = None
    status: Optional[ReferralStatus] = None
    reason: Optional[str] = None
    clinical_notes: Optional[str] = None
    specialist_name: Optional[str] = Field(None, max_length=255)
    specialist_address: Optional[str] = Field(None, max_length=255)
    specialist_phone: Optional[str] = Field(None, max_length=20)
    specialist_fax: Optional[str] = Field(None, max_length=20)
    appointment_date: Optional[datetime] = None
    referral_fee: Optional[Decimal] = None
    referral_received: Optional[bool] = None
    is_urgent: Optional[bool] = None
    urgent_reason: Optional[str] = None

class ReferralResponse(ReferralBase):
    id: UUID
    practice_id: UUID
    referring_provider_id: UUID
    referral_number: str
    referral_date: datetime
    completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
