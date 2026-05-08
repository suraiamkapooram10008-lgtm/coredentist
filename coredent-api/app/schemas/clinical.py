"""
Clinical Schemas
Pydantic models for clinical records and periodontal charts
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

# Perio Chart Entry Schema
class PerioChartEntryBase(BaseModel):
    tooth_number: int = Field(..., ge=1, le=32)
    # Pocket Depths
    pd_distobuccal: Optional[int] = None
    pd_buccal: Optional[int] = None
    pd_mesiobuccal: Optional[int] = None
    pd_distolingual: Optional[int] = None
    pd_lingual: Optional[int] = None
    pd_mesiolingual: Optional[int] = None
    # Bleeding
    bop_distobuccal: bool = False
    bop_buccal: bool = False
    bop_mesiobuccal: bool = False
    bop_distolingual: bool = False
    bop_lingual: bool = False
    bop_mesiolingual: bool = False
    # CAL
    cal_distobuccal: Optional[int] = None
    cal_buccal: Optional[int] = None
    cal_mesiobuccal: Optional[int] = None
    cal_distolingual: Optional[int] = None
    cal_lingual: Optional[int] = None
    cal_mesiolingual: Optional[int] = None
    # Advanced
    mobility: Optional[int] = Field(None, ge=0, le=3)
    furcation_class: Optional[str] = Field(None, max_length=10)
    mucogingival_defect: bool = False
    display_order: int = 0

class PerioChartEntryCreate(PerioChartEntryBase):
    pass

class PerioChartEntryResponse(PerioChartEntryBase):
    id: UUID
    perio_chart_id: UUID
    class Config:
        from_attributes = True

class PerioChartBase(BaseModel):
    patient_id: UUID
    overall_bleeding_index: Optional[float] = None
    plaque_index: Optional[float] = None
    calculus_index: Optional[float] = None
    diagnosis: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None

class PerioChartCreate(PerioChartBase):
    entries: List[PerioChartEntryCreate] = []

class PerioChartResponse(PerioChartBase):
    id: UUID
    provider_id: UUID
    examination_date: datetime
    created_at: datetime
    updated_at: datetime
    entries: List[PerioChartEntryResponse] = []
    class Config:
        from_attributes = True

class PerioChartListResponse(BaseModel):
    perio_charts: List[PerioChartResponse]
    count: int
