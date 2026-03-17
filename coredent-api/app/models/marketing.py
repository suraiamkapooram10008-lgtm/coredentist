"""
Marketing Models
Email campaigns, newsletters, and marketing automation
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Boolean, Integer, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class CampaignStatus(str, enum.Enum):
    """Campaign status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class CampaignType(str, enum.Enum):
    """Campaign types"""
    EMAIL = "email"
    SMS = "sms"
    NEWSLETTER = "newsletter"
    PROMOTION = "promotion"
    RECALL = "recall"
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    CUSTOM = "custom"


class AudienceType(str, enum.Enum):
    """Audience types"""
    ALL_PATIENTS = "all_patients"
    ACTIVE_PATIENTS = "active_patients"
    INACTIVE_PATIENTS = "inactive_patients"
    NEW_PATIENTS = "new_patients"
    RECALL_DUE = "recall_due"
    INSURANCE_TYPE = "insurance_type"
    CUSTOM = "custom"


class Campaign(Base):
    """Marketing campaign model"""
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Campaign Information
    name = Column(String(255), nullable=False)
    subject = Column(String(255))  # For email
    campaign_type = Column(Enum(CampaignType), nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    
    # Content
    content = Column(Text)  # HTML for email, text for SMS
    template_id = Column(UUID(as_uuid=True), ForeignKey("marketing_templates.id"))
    
    # Audience
    audience_type = Column(Enum(AudienceType), default=AudienceType.ALL_PATIENTS)
    audience_filters = Column(JSON)  # JSON object of filters
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Stats
    total_recipients = Column(Integer, default=0)
    successful_sends = Column(Integer, default=0)
    failed_sends = Column(Integer, default=0)
    opens = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    unsubscribes = Column(Integer, default=0)
    bounces = Column(Integer, default=0)
    
    # Financial
    cost = Column(Numeric(10, 2), default=0)
    
    # Settings
    track_opens = Column(Boolean, default=True)
    track_clicks = Column(Boolean, default=True)
    allow_unsubscribe = Column(Boolean, default=True)
    
    # Parent Campaign (for A/B testing)
    parent_campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="campaigns")
    creator = relationship("User")
    template = relationship("MarketingTemplate")
    segments = relationship("CampaignSegment", back_populates="campaign")
    emails = relationship("MarketingEmail", back_populates="campaign")
    
    def __repr__(self):
        return f"<Campaign {self.name} - {self.status}>"


class MarketingTemplate(Base):
    """Marketing email/SMS template"""
    __tablename__ = "marketing_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    
    # Template Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    
    # Content
    subject = Column(String(255))
    content = Column(Text, nullable=False)  # HTML or text
    preview_text = Column(String(255))  # Preview text for email
    
    # Design
    template_type = Column(String(20))  # custom, drag_drop
    layout_config = Column(JSON)  # JSON for drag-drop layout
    
    # Footer
    unsubscribe_text = Column(Text)
    physical_address = Column(Text)
    
    # Variables
    available_variables = Column(JSON)  # JSON array of available merge tags
    
    # Status
    is_active = Column(Boolean, default=True)
    is_shared = Column(Boolean, default=False)  # Available to all practices
    
    # Usage
    times_used = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="marketing_templates")
    campaigns = relationship("Campaign", back_populates="template")
    
    def __repr__(self):
        return f"<MarketingTemplate {self.name}>"


class CampaignSegment(Base):
    """Campaign audience segment"""
    __tablename__ = "campaign_segments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    
    # Segment Information
    name = Column(String(255), nullable=False)
    segment_type = Column(String(50))  # A, B, control
    
    # Filters
    filters = Column(JSON)  # JSON object of segment criteria
    
    # Count
    recipient_count = Column(Integer, default=0)
    
    # Stats (for this segment)
    sent = Column(Integer, default=0)
    opens = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="segments")
    
    def __repr__(self):
        return f"<CampaignSegment {self.name}>"


class MarketingEmail(Base):
    """Individual marketing email record"""
    __tablename__ = "marketing_emails"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    
    # Email Information
    recipient_email = Column(String(255), nullable=False)
    recipient_name = Column(String(255))
    
    # Content (rendered for this recipient)
    subject = Column(String(255))
    content = Column(Text)
    
    # Status
    status = Column(String(20), default="pending")  # pending, sent, opened, clicked, bounced, unsubscribed
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    clicked_at = Column(DateTime(timezone=True))
    bounced_at = Column(DateTime(timezone=True))
    
    # External IDs
    message_id = Column(String(100))  # ESP message ID
    
    # Error
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="emails")
    patient = relationship("Patient")
    
    def __repr__(self):
        return f"<MarketingEmail {self.recipient_email}>"


class NewsletterSubscription(Base):
    """Newsletter subscription management"""
    __tablename__ = "newsletter_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    
    # Subscriber Information
    email = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    
    # Source
    source = Column(String(50))  # website, in_office, referral, etc.
    
    # Preferences
    subscribed = Column(Boolean, default=True)
    subscribed_at = Column(DateTime(timezone=True))
    unsubscribed_at = Column(DateTime(timezone=True))
    
    # Newsletter Types
    newsletter_types = Column(JSON)  # JSON array of subscribed types
    
    # GDPR
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(20), default="active")  # active, unsubscribed, bounced
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="newsletter_subscriptions")
    
    def __repr__(self):
        return f"<NewsletterSubscription {self.email}>"
