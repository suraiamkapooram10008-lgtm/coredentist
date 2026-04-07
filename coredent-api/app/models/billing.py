"""
Billing Models
Invoices and payments
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Numeric, Date, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.base import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice status"""
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    """Payment methods"""
    CASH = "cash"
    CARD = "card"
    CHECK = "check"
    INSURANCE = "insurance"
    UPI = "upi"  # Indian UPI payments
    OTHER = "other"


class PaymentStatus(str, enum.Enum):
    """Payment status"""
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentPlanStatus(str, enum.Enum):
    """Payment plan status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class Invoice(Base):
    """Invoice model"""
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING)
    
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)
    
    # GST fields (Indian compliance)
    gstin = Column(String(15))  # GST Identification Number
    gst_rate = Column(Numeric(5, 2), default=18.00)  # Default 18%
    cgst_amount = Column(Numeric(10, 2), default=0)
    sgst_amount = Column(Numeric(10, 2), default=0)
    igst_amount = Column(Numeric(10, 2), default=0)
    is_inter_state = Column(String(1), default="N")  # Y/N for inter-state
    
    # Line items stored as JSON
    # Structure: [{ description: "", quantity: 1, unit_price: 0, total: 0 }]
    line_items = Column(JSON, nullable=False)
    
    due_date = Column(Date)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="invoices")
    patient = relationship("Patient", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    
    @property
    def amount_paid(self) -> float:
        """Calculate total amount paid"""
        return sum(float(p.amount) for p in self.payments if p.status == PaymentStatus.COMPLETED)
    
    @property
    def balance_due(self) -> float:
        """Calculate remaining balance"""
        return float(self.total) - self.amount_paid
    
    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.status}>"


class Payment(Base):
    """Payment model"""
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    transaction_id = Column(String(255))
    status = Column(Enum(PaymentStatus), default=PaymentStatus.COMPLETED)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    patient = relationship("Patient", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment {self.id} - ${self.amount}>"


class PaymentPlan(Base):
    """Installment-based payment plan"""
    __tablename__ = "payment_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    
    status = Column(Enum(PaymentPlanStatus), default=PaymentPlanStatus.ACTIVE)
    total_amount = Column(Numeric(10, 2), nullable=False)
    initial_deposit = Column(Numeric(10, 2), default=0)
    interest_rate = Column(Numeric(5, 2), default=0)  # Annual percentage rate
    
    start_date = Column(Date, nullable=False)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice")
    patient = relationship("Patient")
    invoice = relationship("Invoice")
    installments = relationship("PaymentPlanInstallment", back_populates="plan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PaymentPlan {self.id} - {self.status}>"


class PaymentPlanInstallment(Base):
    """Individual installment in a payment plan"""
    __tablename__ = "payment_plan_installments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("payment_plans.id"), nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="scheduled")  # scheduled, paid, overdue
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    plan = relationship("PaymentPlan", back_populates="installments")
    
    def __repr__(self):
        return f"<Installment {self.id} - ${self.amount} - {self.status}>"
