"""
User Model
Represents staff members and system users
SECURITY: Added database indexes for query performance
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles for RBAC"""
    OWNER = "owner"
    ADMIN = "admin"
    DENTIST = "dentist"
    HYGIENIST = "hygienist"
    FRONT_DESK = "front_desk"


class User(Base):
    """User/Staff member model"""
    __tablename__ = "users"
    
    # PERFORMANCE: Add composite indexes
    __table_args__ = (
        Index('idx_user_practice_role', 'practice_id', 'role'),
        Index('idx_user_practice_active', 'practice_id', 'is_active'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="users")
    appointments = relationship("Appointment", back_populates="provider")
    clinical_notes = relationship("ClinicalNote", back_populates="provider")
    treatment_plans = relationship("TreatmentPlan", back_populates="provider")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    images = relationship("PatientImage", back_populates="provider")
    online_bookings = relationship("OnlineBooking", back_populates="provider")
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
