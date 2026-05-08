"""
Clinical Models
Clinical notes, dental charts, and treatment plans
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.base import Base


class NoteType(str, enum.Enum):
    """Clinical note types"""
    SOAP = "soap"
    PROGRESS = "progress"
    TREATMENT = "treatment"
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"

class ConditionType(str, enum.Enum):
    """Types of dental conditions"""
    CARIES = "caries"
    FRACTURE = "fracture"
    MISSING = "missing"
    IMPACTED = "impacted"
    WEAR = "wear"
    EROSION = "erosion"
    ABSCESS = "abscess"
    ROOT_REMNANT = "root_remnant"
    EXISTING_RESTORATION = "existing_restoration"
    DEFECTIVE_RESTORATION = "defective_restoration"

class RestorationStatus(str, enum.Enum):
    """Status of a condition/restoration"""
    EXISTING = "existing"
    PLANNED = "planned"
    COMPLETED = "completed"

class SurfaceCode(str, enum.Enum):
    """Tooth surfaces"""
    MESIAL = "M"
    OCCLUSAL = "O"
    DISTAL = "D"
    BUCCAL = "B"
    LINGUAL = "L"
    INCISAL = "I"
    FACIAL = "F"


class ClinicalNote(Base):
    """Clinical note model"""
    __tablename__ = "clinical_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"))
    
    note_type = Column(Enum(NoteType), nullable=False)
    content = Column(Text, nullable=False)
    attachments = Column(JSON, default=[])  # Array of file URLs
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="clinical_notes")
    provider = relationship("User", back_populates="clinical_notes")
    
    def __repr__(self):
        return f"<ClinicalNote {self.id} - {self.note_type}>"


class DentalChart(Base):
    """Dental chart model"""
    __tablename__ = "dental_charts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), unique=True, nullable=False)
    
    # Chart data stored as JSON
    # Structure: { tooth_number: { conditions: [], procedures: [], notes: "" } }
    chart_data = Column(JSON, nullable=False, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="dental_chart")
    
    def __repr__(self):
        return f"<DentalChart for Patient {self.patient_id}>"


class ToothCondition(Base):
    """Individual tooth condition record for visual charting"""
    __tablename__ = "tooth_conditions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    tooth_number = Column(String(10), nullable=False)
    surface = Column(String(10))  # Can be multiple surfaces like "MOD"
    condition_type = Column(Enum(ConditionType), nullable=False)
    status = Column(Enum(RestorationStatus), default=RestorationStatus.EXISTING)
    severity = Column(String(50))
    
    material = Column(String(100))  # e.g., "Amalgam", "Composite", "Gold"
    notes = Column(Text)
    noted_date = Column(DateTime(timezone=True), server_default=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    patient = relationship("Patient")
    provider = relationship("User")


class ChartingEntry(Base):
    """Historical timeline of charting events"""
    __tablename__ = "charting_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    tooth_number = Column(String(10))
    entry_type = Column(String(50))  # "condition", "procedure", "note"
    data = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    patient = relationship("Patient")
    provider = relationship("User")


class ChartingSymbol(Base):
    """Custom graphical symbols for visual charting"""
    __tablename__ = "charting_symbols"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    symbol_type = Column(String(50))  # "crown", "bridge", "implant", etc.
    category = Column(String(50))
    svg_data = Column(Text)  # The raw SVG path/element data
    color = Column(String(20))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    practice = relationship("Practice")


class PerioChart(Base):
    """Periodontal charting model - records probing depths, bleeding points, mobility"""
    __tablename__ = "perio_charts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    examination_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Perio data stored as JSON
    # Structure: { tooth_number: { probing_depths: [1,2,3...], bleeding_points: [], mobility: "", furcation: "" } }
    perio_data = Column(JSON, nullable=False, default={})
    
    # Overall assessment
    overall_bleeding_index = Column(Numeric(5, 2))  # 0-100%
    plaque_index = Column(Numeric(5, 2))  # 0-100%
    calculus_index = Column(Numeric(5, 2))  # 0-100%
    diagnosis = Column(String(255))  # e.g., "Healthy", "Gingivitis", "Periodontitis"
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="perio_charts")
    provider = relationship("User")
    entries = relationship("PerioChartEntry", back_populates="perio_chart", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PerioChart for Patient {self.patient_id} on {self.examination_date}>"


class PerioChartEntry(Base):
    """Individual periodontal measurement entry for a tooth"""
    __tablename__ = "perio_chart_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    perio_chart_id = Column(UUID(as_uuid=True), ForeignKey("perio_charts.id"), nullable=False)
    
    # Tooth identification
    tooth_number = Column(String(10), nullable=False)  # e.g., "1", "2", "1A"
    
    # Probing depths (6 sites per tooth: MB, B, DB, ML, L, DL)
    probing_depths = Column(JSON, default=list)  # [3, 2, 3, 4, 3, 2]
    
    # Bleeding on probing (6 sites)
    bleeding_points = Column(JSON, default=list)  # [True, False, True, ...]
    
    # Additional measurements
    recession = Column(JSON, default=list)  # [1, 0, 0, 2, 1, 0]
    attachment_level = Column(JSON, default=list)  # Calculated
    
    # Tooth condition
    mobility = Column(String(10))  # "0", "I", "II", "III"
    furcation = Column(String(10))  # "0", "I", "II", "III"
    
    # Notes for this tooth
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    perio_chart = relationship("PerioChart", back_populates="entries")
    
    def __repr__(self):
        return f"<PerioChartEntry Tooth {self.tooth_number}>"
