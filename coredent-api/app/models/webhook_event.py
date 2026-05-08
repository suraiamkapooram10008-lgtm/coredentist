"""
Webhook Event Model
Tracks processed webhook events for idempotency
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from app.core.base import Base


class WebhookEvent(Base):
    """
    Webhook event tracking for idempotency.
    Prevents duplicate processing of webhook events.
    """
    __tablename__ = "webhook_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Webhook provider (stripe, razorpay, etc.)
    provider = Column(String(50), nullable=False, index=True)
    
    # Unique event ID from provider
    event_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Event type (payment.succeeded, subscription.created, etc.)
    event_type = Column(String(100), nullable=False)
    
    # Processing status
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    payload_hash = Column(String(64), nullable=True)  # SHA-256 hash of payload
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_webhook_provider_event', 'provider', 'event_id'),
        Index('idx_webhook_processed', 'processed', 'created_at'),
    )
    
    def __repr__(self):
        return f"<WebhookEvent {self.provider}:{self.event_id} processed={self.processed}>"
