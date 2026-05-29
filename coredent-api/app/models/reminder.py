"""Reminder model for scheduling notifications."""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.base import Base
import uuid
import enum


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False
    )
    reminder_type = Column(String(50), nullable=False)  # sms, email
    status = Column(Enum(ReminderStatus), default=ReminderStatus.PENDING)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True))
    error_message = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
