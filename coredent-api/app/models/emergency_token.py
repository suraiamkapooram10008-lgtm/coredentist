"""
Emergency Token Model
Database-backed storage for emergency (break-glass) tokens.
M-1 FIX: Migrated from in-memory dict to database for multi-instance support.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.base import Base


class EmergencyToken(Base):
    """Emergency break-glass token stored in database"""
    __tablename__ = "emergency_tokens"

    __table_args__ = (
        Index('idx_emergency_token_hash', 'token_hash'),
        Index('idx_emergency_token_expires', 'expires_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(255), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Text, nullable=False)
    authorized_by = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)

    def __repr__(self):
        return f"<EmergencyToken user_id={self.user_id} expires={self.expires_at} used={self.used}>"