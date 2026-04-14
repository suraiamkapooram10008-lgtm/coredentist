"""
Clinic Settings Schemas
Pydantic models for clinic/practice settings
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ClinicSettingsResponse(BaseModel):
    """Clinic settings response"""
    id: str
    name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zipCode: str
    country: str
    timezone: str
    website: str
    logo: str
    workingHours: Dict[str, Any]
    appointmentTypes: List[Dict[str, Any]]
    chairs: List[Dict[str, Any]]


class ClinicSettingsUpdate(BaseModel):
    """Clinic settings update"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    website: Optional[str] = None
    logo: Optional[str] = None
    workingHours: Optional[Dict[str, Any]] = None
    appointmentTypes: Optional[List[Dict[str, Any]]] = None
    chairs: Optional[List[Dict[str, Any]]] = None
