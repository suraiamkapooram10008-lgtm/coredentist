"""
Appointment Schemas
Pydantic models for appointment data validation
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from uuid import UUID

from app.models.appointment import AppointmentStatus, AppointmentTypeEnum


class AppointmentBase(BaseModel):
    """Base appointment schema"""
    patient_id: UUID
    provider_id: Optional[UUID] = None
    chair_id: Optional[UUID] = None
    appointment_type: AppointmentTypeEnum
    status: Optional[AppointmentStatus] = AppointmentStatus.SCHEDULED
    start_time: datetime
    end_time: datetime
    duration: int = Field(..., gt=0, description="Duration in minutes")
    notes: Optional[str] = None
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
    
    @validator('duration')
    def validate_duration(cls, v, values):
        if 'start_time' in values and 'end_time' in values:
            expected_duration = int((values['end_time'] - values['start_time']).total_seconds() / 60)
            if v != expected_duration:
                raise ValueError(f'duration must match time difference ({expected_duration} minutes)')
        return v


class AppointmentCreate(AppointmentBase):
    """Schema for creating appointments"""
    pass


class AppointmentUpdate(BaseModel):
    """Schema for updating appointments"""
    provider_id: Optional[UUID] = None
    chair_id: Optional[UUID] = None
    appointment_type: Optional[AppointmentTypeEnum] = None
    status: Optional[AppointmentStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    """Schema for appointment responses"""
    id: UUID
    practice_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """Schema for list of appointments"""
    appointments: List[AppointmentResponse]
    count: int


class AppointmentSlot(BaseModel):
    """Schema for available appointment slots"""
    start_time: datetime
    end_time: datetime
    duration: int
    is_available: bool