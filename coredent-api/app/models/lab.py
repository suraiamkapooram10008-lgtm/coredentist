"""
Lab Management Models
Case tracking, lab orders, and invoicing
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Numeric, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class LabCaseStatus(str, enum.Enum):
    """Lab case status"""
    PENDING = "pending"
    SENT = "sent"
    IN_PROGRESS = "in_progress"
    QUALITY_CHECK = "quality_check"
    READY_TO_SHIP = "ready_to_ship"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    REFUSED = "refused"


class LabCaseType(str, enum.Enum):
    """Types of lab cases"""
    CROWN = "crown"
    BRIDGE = "bridge"
    DENTURE = "denture"
    PARTIAL = "partial"
    IMPLANT = "implant"
    ORTHODONTIC = "orthodontic"
    BLEACHING_TRAY = "bleaching_tray"
    NIGHT_GUARD = "night_guard"
    SPORTS_GUARD = "sports_guard"
    OTHER = "other"


class LabOrderStatus(str, enum.Enum):
    """Lab order status"""
    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Lab(Base):
    """Dental lab/vendor model"""
    __tablename__ = "labs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    
    # Lab Information
    name = Column(String(255), nullable=False)
    contact_name = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    fax = Column(String(20))
    website = Column(String(255))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))
    
    # Account Information
    account_number = Column(String(50))
    payment_terms = Column(String(50))
    
    # Services
    services_offered = Column(Text)  # JSON array of services
    
    # Status
    is_active = Column(Boolean, default=True)
    is_preferred = Column(Boolean, default=False)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="labs")
    cases = relationship("LabCase", back_populates="lab")
    
    def __repr__(self):
        return f"<Lab {self.name}>"


class LabCase(Base):
    """Lab case model - tracks cases sent to lab"""
    __tablename__ = "lab_cases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    lab_id = Column(UUID(as_uuid=True), ForeignKey("labs.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Case Information
    case_number = Column(String(50), unique=True, nullable=False)
    case_type = Column(Enum(LabCaseType), nullable=False)
    status = Column(Enum(LabCaseStatus), default=LabCaseStatus.PENDING)
    
    # Description
    description = Column(Text)
    shade = Column(String(50))
    shade_notes = Column(Text)
    
    # Teeth Involved
    teeth_involved = Column(String(100))  # e.g., "3,4,5" or "FDI: 45,46"
    
    # Dates
    sent_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    received_date = Column(DateTime(timezone=True))
    delivered_date = Column(DateTime(timezone=True))
    
    # Financial
    case_cost = Column(Numeric(10, 2))
    case_price = Column(Numeric(10, 2))
    patient_charge = Column(Numeric(10, 2))
    insurance_estimate = Column(Numeric(10, 2))
    
    # Shipping
    tracking_number = Column(String(100))
    shipping_method = Column(String(50))
    shipping_cost = Column(Numeric(10, 2))
    
    # Notes
    provider_notes = Column(Text)
    lab_notes = Column(Text)
    internal_notes = Column(Text)
    
    # Attachments
    prescriptions = Column(Text)  # JSON array of file URLs
    impressions = Column(Text)  # JSON array of file URLs
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="lab_cases")
    lab = relationship("Lab", back_populates="cases")
    patient = relationship("Patient", back_populates="lab_cases")
    provider = relationship("User")
    invoices = relationship("LabInvoice", back_populates="lab_case")
    
    def __repr__(self):
        return f"<LabCase {self.case_number} - {self.status}>"


class LabInvoice(Base):
    """Lab invoice model"""
    __tablename__ = "lab_invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    lab_id = Column(UUID(as_uuid=True), ForeignKey("labs.id"), nullable=False)
    lab_case_id = Column(UUID(as_uuid=True), ForeignKey("lab_cases.id"))
    
    # Invoice Information
    invoice_number = Column(String(50), unique=True, nullable=False)
    invoice_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String(20), default="pending")  # pending, paid, partial, overdue, cancelled
    
    # Financial
    subtotal = Column(Numeric(10, 2), default=0)
    tax = Column(Numeric(10, 2), default=0)
    shipping = Column(Numeric(10, 2), default=0)
    discount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), default=0)
    
    # Payments
    amount_paid = Column(Numeric(10, 2), default=0)
    payment_date = Column(DateTime(timezone=True))
    
    # Notes
    notes = Column(Text)
    terms = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="lab_invoices")
    lab = relationship("Lab", back_populates="invoices")
    lab_case = relationship("LabCase", back_populates="invoices")
    
    @property
    def balance_due(self) -> float:
        return float(self.total or 0) - float(self.amount_paid or 0)
    
    def __repr__(self):
        return f"<LabInvoice {self.invoice_number} - {self.status}>"


class LabCommunication(Base):
    """Lab communication log"""
    __tablename__ = "lab_communications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lab_case_id = Column(UUID(as_uuid=True), ForeignKey("lab_cases.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Communication Details
    communication_type = Column(String(20), nullable=False)  # note, email, phone, message
    subject = Column(String(255))
    content = Column(Text)
    direction = Column(String(10))  # inbound, outbound
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    lab_case = relationship("LabCase", back_populates="communications")
    user = relationship("User")
    
    def __repr__(self):
        return f"<LabCommunication {self.communication_type} for Case {self.lab_case_id}>"
