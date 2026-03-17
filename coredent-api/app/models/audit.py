"""
Audit Models
Audit logs and user sessions for HIPAA compliance
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class AuditLog(Base):
    """Audit log for HIPAA compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    action = Column(String(100), nullable=False)  # e.g., "patient_viewed", "record_updated"
    entity_type = Column(String(50), nullable=False)  # e.g., "patient", "appointment"
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    changes = Column(JSON)  # Before/after values for updates
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}>"


class Session(Base):
    """User session for JWT refresh tokens"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    refresh_token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<Session {self.id} for User {self.user_id}>"
