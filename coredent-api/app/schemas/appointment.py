"""
Appointment Schemas
Pydantic models for appointment validation
"""

from typing import Optional, Union, Any
from uuid import UUID
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator


class AppointmentBase(BaseModel):
    """Base appointment schema"""
    patient_id: UUID
    provider_id: UUID
    chair_id: Optional[Any] = None  # Accepts str or UUID for response validation
    appointment_type: str
    type: Optional[str] = None  # Alias for test compatibility
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def map_type_alias(cls, data):
        if isinstance(data, dict):
            if data.get('type') and not data.get('appointment_type'):
                data['appointment_type'] = data['type']
        return data


class AppointmentCreate(AppointmentBase):
    """Schema for creating appointments"""
    status: Optional[str] = None
    duration: Optional[int] = None


class AppointmentUpdate(BaseModel):
    """Schema for updating appointments"""
    provider_id: Optional[UUID] = None
    chair_id: Optional[str] = None
    appointment_type: Optional[str] = None
    type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def map_type_alias(cls, data):
        if isinstance(data, dict):
            if data.get('type') and not data.get('appointment_type'):
                data['appointment_type'] = data['type']
        return data


class AppointmentResponse(AppointmentBase):
    """Schema for appointment responses"""
    id: UUID
    status: str
    reminder_sent: bool
    confirmed_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """Schema for paginated appointment list responses"""
    appointments: list[AppointmentResponse]
    count: int


class AppointmentSlot(BaseModel):
    """Schema for available appointment slots"""
    start_time: datetime
    end_time: datetime
    duration: int
    is_available: bool
    provider_id: Optional[UUID] = None
    chair_id: Optional[UUID] = None
