"""
Clinical Models
Clinical notes, dental charts, and treatment plans
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON, Numeric
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
    
    def __repr__(self):
        return f"<PerioChart for Patient {self.patient_id} on {self.examination_date}>"
