"""
Treatment Planning Schemas
Pydantic models for treatment planning API
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
import uuid as uuid_lib
from enum import Enum

from app.models.treatment import (
    TreatmentPlanStatus,
    ProcedureType,
    ToothSurface,
)


# Base Schemas
class TreatmentPlanBase(BaseModel):
    """Base treatment plan schema"""
    plan_name: str = Field(..., min_length=1, max_length=255)
    status: TreatmentPlanStatus = TreatmentPlanStatus.DRAFT
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_goals: Optional[str] = None
    target_start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    notes: Optional[str] = None
    visual_config: Dict[str, Any] = Field(default_factory=dict)


class TreatmentPlanCreate(TreatmentPlanBase):
    """Schema for creating a treatment plan"""
    patient_id: uuid_lib.UUID
    provider_id: uuid_lib.UUID


class TreatmentPlanUpdate(BaseModel):
    """Schema for updating a treatment plan"""
    plan_name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[TreatmentPlanStatus] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_goals: Optional[str] = None
    target_start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    acceptance_method: Optional[str] = None
    acceptance_notes: Optional[str] = None
    notes: Optional[str] = None
    visual_config: Optional[Dict[str, Any]] = None


class TreatmentPlanResponse(TreatmentPlanBase):
    """Schema for treatment plan response"""
    id: uuid_lib.UUID
    practice_id: uuid_lib.UUID
    patient_id: uuid_lib.UUID
    provider_id: uuid_lib.UUID
    total_estimated_cost: float
    total_insurance_estimate: float
    total_patient_responsibility: float
    created_date: date
    presented_date: Optional[date] = None
    accepted_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TreatmentPlanListResponse(BaseModel):
    """Schema for listing treatment plans"""
    plans: List[TreatmentPlanResponse]
    count: int


# Treatment Phase Schemas
class TreatmentPhaseBase(BaseModel):
    """Base treatment phase schema"""
    phase_number: int = Field(..., ge=1)
    phase_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    status: str = "planned"
    display_order: int = 0


class TreatmentPhaseCreate(TreatmentPhaseBase):
    """Schema for creating a treatment phase"""
    pass


class TreatmentPhaseUpdate(BaseModel):
    """Schema for updating a treatment phase"""
    phase_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    status: Optional[str] = None
    display_order: Optional[int] = None
    actual_start_date: Optional[date] = None
    actual_completion_date: Optional[date] = None


class TreatmentPhaseResponse(TreatmentPhaseBase):
    """Schema for treatment phase response"""
    id: uuid_lib.UUID
    treatment_plan_id: uuid_lib.UUID
    estimated_cost: float
    insurance_estimate: float
    patient_responsibility: float
    actual_start_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TreatmentPhaseListResponse(BaseModel):
    """Schema for listing treatment phases"""
    phases: List[TreatmentPhaseResponse]
    count: int


# Treatment Procedure Schemas
class ProcedureSurface(BaseModel):
    """Schema for tooth surfaces"""
    surface: ToothSurface
    description: Optional[str] = None


class TreatmentProcedureBase(BaseModel):
    """Base treatment procedure schema"""
    procedure_type: ProcedureType
    ada_code: str = Field(..., min_length=4, max_length=10)
    description: str = Field(..., min_length=1, max_length=500)
    tooth_number: Optional[str] = None
    surfaces: Optional[str] = None
    quadrant: Optional[int] = Field(None, ge=1, le=4)
    fee: float = Field(..., ge=0)
    insurance_estimate: float = Field(0, ge=0)
    patient_responsibility: float = Field(0, ge=0)
    is_covered: bool = True
    coverage_percentage: int = Field(0, ge=0, le=100)
    requires_pre_auth: bool = False
    priority: int = Field(1, ge=1, le=3)
    complexity: Optional[str] = None
    duration_minutes: int = Field(30, ge=1)
    status: str = "planned"
    is_accepted: bool = False
    acceptance_notes: Optional[str] = None
    display_order: int = 0


class TreatmentProcedureCreate(TreatmentProcedureBase):
    """Schema for creating a treatment procedure"""
    phase_id: Optional[uuid_lib.UUID] = None


class TreatmentProcedureUpdate(BaseModel):
    """Schema for updating a treatment procedure"""
    procedure_type: Optional[ProcedureType] = None
    ada_code: Optional[str] = Field(None, min_length=4, max_length=10)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    tooth_number: Optional[str] = None
    surfaces: Optional[str] = None
    quadrant: Optional[int] = Field(None, ge=1, le=4)
    fee: Optional[float] = Field(None, ge=0)
    insurance_estimate: Optional[float] = Field(None, ge=0)
    patient_responsibility: Optional[float] = Field(None, ge=0)
    is_covered: Optional[bool] = None
    coverage_percentage: Optional[int] = Field(None, ge=0, le=100)
    requires_pre_auth: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    complexity: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=1)
    status: Optional[str] = None
    is_accepted: Optional[bool] = None
    acceptance_notes: Optional[str] = None
    display_order: Optional[int] = None
    appointment_id: Optional[uuid_lib.UUID] = None
    pre_auth_id: Optional[uuid_lib.UUID] = None


class TreatmentProcedureResponse(TreatmentProcedureBase):
    """Schema for treatment procedure response"""
    id: uuid_lib.UUID
    treatment_plan_id: uuid_lib.UUID
    phase_id: Optional[uuid_lib.UUID] = None
    appointment_id: Optional[uuid_lib.UUID] = None
    pre_auth_id: Optional[uuid_lib.UUID] = None
    created_at: datetime
    updated_at: datetime
    
    @property
    def insurance_coverage_amount(self) -> float:
        return self.fee * (self.coverage_percentage / 100)
    
    @property
    def patient_amount(self) -> float:
        return self.fee - self.insurance_coverage_amount
    
    class Config:
        from_attributes = True


class TreatmentProcedureListResponse(BaseModel):
    """Schema for listing treatment procedures"""
    procedures: List[TreatmentProcedureResponse]
    count: int


# Procedure Library Schemas
class ProcedureLibraryBase(BaseModel):
    """Base procedure library schema"""
    ada_code: str = Field(..., min_length=4, max_length=10)
    description: str = Field(..., min_length=1, max_length=500)
    long_description: Optional[str] = None
    procedure_type: ProcedureType
    category: Optional[str] = None
    subcategory: Optional[str] = None
    default_fee: Optional[float] = None
    typical_duration_minutes: int = Field(30, ge=1)
    typical_coverage_percentage: Optional[int] = Field(None, ge=0, le=100)
    requires_pre_auth: bool = False
    common_alternatives: Optional[str] = None
    is_active: bool = True


class ProcedureLibraryCreate(ProcedureLibraryBase):
    """Schema for creating a procedure library entry"""
    pass


class ProcedureLibraryUpdate(BaseModel):
    """Schema for updating a procedure library entry"""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    long_description: Optional[str] = None
    procedure_type: Optional[ProcedureType] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    default_fee: Optional[float] = None
    typical_duration_minutes: Optional[int] = Field(None, ge=1)
    typical_coverage_percentage: Optional[int] = Field(None, ge=0, le=100)
    requires_pre_auth: Optional[bool] = None
    common_alternatives: Optional[str] = None
    is_active: Optional[bool] = None
    is_archived: Optional[bool] = None


class ProcedureLibraryResponse(ProcedureLibraryBase):
    """Schema for procedure library response"""
    id: uuid_lib.UUID
    practice_id: uuid_lib.UUID
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProcedureLibraryListResponse(BaseModel):
    """Schema for listing procedure library entries"""
    procedures: List[ProcedureLibraryResponse]
    count: int


# Treatment Plan Template Schemas
class TemplateProcedure(BaseModel):
    """Schema for template procedure configuration"""
    ada_code: str
    description: str
    default_fee: Optional[float] = None
    typical_duration_minutes: Optional[int] = None
    typical_coverage_percentage: Optional[int] = None


class TreatmentPlanTemplateBase(BaseModel):
    """Base treatment plan template schema"""
    template_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    typical_diagnosis: Optional[str] = None
    typical_goals: Optional[str] = None
    configuration: List[TemplateProcedure] = Field(default_factory=list)
    is_active: bool = True


class TreatmentPlanTemplateCreate(TreatmentPlanTemplateBase):
    """Schema for creating a treatment plan template"""
    pass


class TreatmentPlanTemplateUpdate(BaseModel):
    """Schema for updating a treatment plan template"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    typical_diagnosis: Optional[str] = None
    typical_goals: Optional[str] = None
    configuration: Optional[List[TemplateProcedure]] = None
    is_active: Optional[bool] = None


class TreatmentPlanTemplateResponse(TreatmentPlanTemplateBase):
    """Schema for treatment plan template response"""
    id: uuid_lib.UUID
    practice_id: uuid_lib.UUID
    usage_count: int
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TreatmentPlanTemplateListResponse(BaseModel):
    """Schema for listing treatment plan templates"""
    templates: List[TreatmentPlanTemplateResponse]
    count: int


# Treatment Plan Note Schemas
class TreatmentPlanNoteBase(BaseModel):
    """Base treatment plan note schema"""
    note_type: str = "general"
    content: str = Field(..., min_length=1)
    attachments: List[str] = Field(default_factory=list)
    is_internal: bool = True


class TreatmentPlanNoteCreate(TreatmentPlanNoteBase):
    """Schema for creating a treatment plan note"""
    pass


class TreatmentPlanNoteUpdate(BaseModel):
    """Schema for updating a treatment plan note"""
    note_type: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    attachments: Optional[List[str]] = None
    is_internal: Optional[bool] = None


class TreatmentPlanNoteResponse(TreatmentPlanNoteBase):
    """Schema for treatment plan note response"""
    id: uuid_lib.UUID
    treatment_plan_id: uuid_lib.UUID
    author_id: uuid_lib.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TreatmentPlanNoteListResponse(BaseModel):
    """Schema for listing treatment plan notes"""
    notes: List[TreatmentPlanNoteResponse]
    count: int


# Cost Estimate Schemas
class CostEstimateRequest(BaseModel):
    """Schema for cost estimate request"""
    procedures: List[TreatmentProcedureCreate]
    patient_insurance_id: Optional[uuid_lib.UUID] = None


class CostEstimateResponse(BaseModel):
    """Schema for cost estimate response"""
    total_fee: float
    total_insurance_estimate: float
    total_patient_responsibility: float
    procedure_estimates: List[Dict[str, Any]]
    insurance_details: Optional[Dict[str, Any]] = None


# Acceptance Tracking Schemas
class PlanAcceptanceRequest(BaseModel):
    """Schema for plan acceptance request"""
    acceptance_method: str = Field(..., min_length=1)
    acceptance_notes: Optional[str] = None
    accepted_procedures: Optional[List[uuid_lib.UUID]] = None  # Specific procedures accepted


class PlanAcceptanceResponse(BaseModel):
    """Schema for plan acceptance response"""
    plan_id: uuid_lib.UUID
    status: TreatmentPlanStatus
    accepted_date: date
    acceptance_method: str
    total_accepted_cost: float
    accepted_procedures: List[uuid_lib.UUID]


# Visual Builder Schemas
class VisualBuilderConfig(BaseModel):
    """Schema for visual builder configuration"""
    layout: str = "grid"  # grid, list, timeline
    show_tooth_chart: bool = True
    show_cost_breakdown: bool = True
    show_insurance_coverage: bool = True
    show_timeline: bool = True
    color_scheme: str = "professional"  # professional, clinical, patient_friendly
    grouping: str = "phase"  # phase, priority, procedure_type


class ToothChartPosition(BaseModel):
    """Schema for tooth chart position"""
    tooth_number: str
    x: int
    y: int
    rotation: int = 0
    scale: float = 1.0


class VisualBuilderResponse(BaseModel):
    """Schema for visual builder response"""
    plan_id: uuid_lib.UUID
    config: VisualBuilderConfig
    tooth_positions: List[ToothChartPosition]
    visual_data: Dict[str, Any]