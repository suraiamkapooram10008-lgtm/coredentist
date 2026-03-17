"""
Practice Model
Represents dental practices/clinics
"""

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Practice(Base):
    """Practice/Clinic model"""
    __tablename__ = "practices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    address_street = Column(String(255))
    address_city = Column(String(100))
    address_state = Column(String(2))
    address_zip = Column(String(10))
    timezone = Column(String(50), default="America/New_York")
    currency = Column(String(3), default="USD")
    logo_url = Column(String)
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="practice")
    patients = relationship("Patient", back_populates="practice")
    appointments = relationship("Appointment", back_populates="practice")
    chairs = relationship("Chair", back_populates="practice")
    appointment_types = relationship("AppointmentType", back_populates="practice")
    invoices = relationship("Invoice", back_populates="practice")
    insurance_claims = relationship("InsuranceClaim", back_populates="practice")
    images = relationship("PatientImage", back_populates="practice")
    treatment_plans = relationship("TreatmentPlan", back_populates="practice")
    booking_pages = relationship("BookingPage", back_populates="practice")
    online_bookings = relationship("OnlineBooking", back_populates="practice")
    waitlist_entries = relationship("WaitlistEntry", back_populates="practice")
    # New relationships for additional modules
    inventory_items = relationship("InventoryItem", back_populates="practice")
    suppliers = relationship("Supplier", back_populates="practice")
    purchase_orders = relationship("PurchaseOrder", back_populates="practice")
    labs = relationship("Lab", back_populates="practice")
    lab_cases = relationship("LabCase", back_populates="practice")
    lab_invoices = relationship("LabInvoice", back_populates="practice")
    referral_sources = relationship("ReferralSource1", back_populates="practice")
    referrals = relationship("Referral", back_populates="practice")
    referral_reports = relationship("ReferralReport", back_populates="practice")
    message_templates = relationship("MessageTemplate", back_populates="practice")
    patient_messages = relationship("PatientMessage", back_populates="practice")
    reminder_schedules = relationship("ReminderSchedule", back_populates="practice")
    conversations = relationship("Conversation", back_populates="practice")
    document_templates = relationship("DocumentTemplate", back_populates="practice")
    documents = relationship("Document", back_populates="practice")
    campaigns = relationship("Campaign", back_populates="practice")
    marketing_templates = relationship("MarketingTemplate", back_populates="practice")
    newsletter_subscriptions = relationship("NewsletterSubscription", back_populates="practice")
    
    def __repr__(self):
        return f"<Practice {self.name}>"
