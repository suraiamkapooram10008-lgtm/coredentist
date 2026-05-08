"""
Payroll Schemas
Pydantic request/response models for payroll, commissions, timesheets, and production tracking
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class PayTypeEnum(str, Enum):
    SALARY = "salary"
    HOURLY = "hourly"
    CONTRACT = "contract"

class CommissionTypeEnum(str, Enum):
    PRODUCTION_PERCENTAGE = "production_percentage"
    COLLECTION_PERCENTAGE = "collection_percentage"
    PER_PROCEDURE = "per_procedure"
    TIERED = "tiered"

class TimesheetStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class PTOTypeEnum(str, Enum):
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    HOLIDAY = "holiday"
    UNPAID = "unpaid"


# --- Compensation ---
class CompensationCreate(BaseModel):
    user_id: UUID
    pay_type: PayTypeEnum = PayTypeEnum.HOURLY
    pay_rate: float = Field(..., gt=0)
    overtime_rate_multiplier: float = 1.5
    overtime_threshold_hours: float = 40
    commission_enabled: bool = False
    commission_structure_id: Optional[UUID] = None
    effective_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None

class CompensationResponse(CompensationCreate):
    id: UUID
    practice_id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Commission Structure ---
class CommissionStructureCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    commission_type: CommissionTypeEnum
    rate_percentage: Optional[float] = None
    tiers: Optional[List[Dict[str, Any]]] = []
    procedure_rates: Optional[Dict[str, float]] = {}
    applies_to_roles: Optional[List[str]] = []

class CommissionStructureResponse(CommissionStructureCreate):
    id: UUID
    practice_id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Timesheet ---
class TimesheetClockIn(BaseModel):
    notes: Optional[str] = None

class TimesheetClockOut(BaseModel):
    break_minutes: int = Field(default=0, ge=0)
    notes: Optional[str] = None

class TimesheetResponse(BaseModel):
    id: UUID
    user_id: UUID
    practice_id: UUID
    work_date: date
    clock_in: datetime
    clock_out: Optional[datetime] = None
    break_minutes: int = 0
    total_hours: Optional[float] = None
    overtime_hours: float = 0
    status: TimesheetStatusEnum
    approved_by: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# --- Payroll Period ---
class PayrollPeriodCreate(BaseModel):
    period_start: date
    period_end: date
    pay_date: Optional[date] = None

class PayrollPeriodResponse(BaseModel):
    id: UUID
    practice_id: UUID
    period_start: date
    period_end: date
    pay_date: Optional[date] = None
    status: str
    total_gross: float = 0
    total_commissions: float = 0
    total_overtime: float = 0
    total_bonuses: float = 0
    total_deductions: float = 0
    processed_by: Optional[UUID] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

# --- Payroll Entry ---
class PayrollEntryResponse(BaseModel):
    id: UUID
    payroll_period_id: UUID
    user_id: UUID
    regular_hours: float = 0
    overtime_hours: float = 0
    base_pay: float = 0
    overtime_pay: float = 0
    commission_amount: float = 0
    bonus: float = 0
    deductions: Dict[str, Any] = {}
    total_deductions: float = 0
    gross_pay: float = 0
    net_pay: float = 0
    total_production: float = 0
    total_collections: float = 0
    procedures_completed: int = 0
    created_at: datetime
    class Config:
        from_attributes = True

# --- Production ---
class ProductionSummary(BaseModel):
    user_id: UUID
    user_name: str
    role: str
    total_production: float
    total_collections: float
    collection_rate: float
    procedures_completed: int
    avg_production_per_procedure: float

# --- PTO ---
class PTORequestCreate(BaseModel):
    pto_type: PTOTypeEnum
    start_date: date
    end_date: date
    hours_requested: float = Field(..., gt=0)
    reason: Optional[str] = None

class PTORequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    pto_type: PTOTypeEnum
    start_date: date
    end_date: date
    hours_requested: float
    status: str
    approved_by: Optional[UUID] = None
    reason: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class PTOBalanceResponse(BaseModel):
    id: UUID
    user_id: UUID
    pto_type: PTOTypeEnum
    year: int
    balance_hours: float
    used_hours: float
    accrual_rate_per_period: float
    class Config:
        from_attributes = True
