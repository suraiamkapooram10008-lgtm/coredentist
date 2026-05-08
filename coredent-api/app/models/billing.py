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
from decimal import Decimal

from app.core.base import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice status"""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"  # Added
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    VOIDED = "voided"  # Added


class PaymentMethod(str, enum.Enum):
    """Payment methods"""
    CASH = "cash"
    CARD = "card"
    CHECK = "check"
    INSURANCE = "insurance"
    OTHER = "other"


class PaymentStatus(str, enum.Enum):
    """Payment status"""
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"
    REFUNDED = "refunded"


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
    
    # Payment tracking columns (updated when payments are created/refunded)
    amount_paid = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    balance_due = Column(Numeric(10, 2), nullable=True)  # Will be set automatically
    
    # Line items stored as JSON
    # Structure: [{ description: "", quantity: 1, unit_price: 0, total: 0 }]
    line_items = Column(JSON, nullable=False)
    
    due_date = Column(Date)
    notes = Column(Text)
    
    # GST fields for Indian tax compliance
    gstin = Column(String(15), nullable=True)
    gst_rate = Column(Numeric(5, 2), default=18.00)
    cgst_amount = Column(Numeric(10, 2), default=0)
    sgst_amount = Column(Numeric(10, 2), default=0)
    igst_amount = Column(Numeric(10, 2), default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="invoices")
    patient = relationship("Patient", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    payment_plans = relationship("PaymentPlan", back_populates="invoice")
    subscription = relationship("Subscription", back_populates="latest_invoice")
    
    def update_payment_totals(self):
        """Update amount_paid and balance_due based on payments"""
        self.amount_paid = sum(
            float(p.amount) for p in self.payments 
            if p.status == PaymentStatus.COMPLETED
        )
        self.balance_due = float(self.total) - self.amount_paid
    
    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.status}>"


# Event listener to set balance_due before insert if not set
from sqlalchemy import event

@event.listens_for(Invoice, 'before_insert')
def set_invoice_balance_due(mapper, connection, target):
    """Set balance_due to total if not already set"""
    if target.balance_due is None:
        target.balance_due = target.total


class Payment(Base):
    """Payment model"""
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    
    payment_number = Column(String(50), unique=True)  # Added for schema compatibility
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())  # Added
    transaction_id = Column(String(255))
    reference_number = Column(String(255))  # Added for schema compatibility
    status = Column(Enum(PaymentStatus), default=PaymentStatus.COMPLETED)
    notes = Column(Text)
    
    # Refund tracking
    refunded_at = Column(DateTime(timezone=True))  # Added
    refunded_amount = Column(Numeric(10, 2))  # Added
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    patient = relationship("Patient", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment {self.id} - ${self.amount}>"


class PaymentPlanStatus(str, enum.Enum):
    """Payment plan status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFAULTED = "defaulted"


class PaymentPlanInstallmentStatus(str, enum.Enum):
    """Installment status"""
    SCHEDULED = "scheduled"
    PAID = "paid"
    OVERDUE = "overdue"
    WAIVED = "waived"


class PaymentPlan(Base):
    """Payment plan for installment payments"""
    __tablename__ = "payment_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    
    total_amount = Column(Numeric(10, 2), nullable=False)
    initial_deposit = Column(Numeric(10, 2), default=0)
    start_date = Column(Date, nullable=False)
    status = Column(Enum(PaymentPlanStatus), default=PaymentPlanStatus.ACTIVE)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("Practice", back_populates="payment_plans")
    patient = relationship("Patient", back_populates="payment_plans")
    invoice = relationship("Invoice", back_populates="payment_plans")
    installments = relationship("PaymentPlanInstallment", back_populates="plan", cascade="all, delete-orphan")
    
    @property
    def amount_paid(self) -> float:
        """Calculate total amount paid"""
        return sum(float(i.amount) for i in self.installments if i.status == PaymentPlanInstallmentStatus.PAID)
    
    @property
    def balance_due(self) -> float:
        """Calculate remaining balance"""
        return float(self.total_amount) - self.amount_paid
    
    def __repr__(self):
        return f"<PaymentPlan {self.id} - {self.status}>"


class PaymentPlanInstallment(Base):
    """Individual installment within a payment plan"""
    __tablename__ = "payment_plan_installments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("payment_plans.id"), nullable=False)
    
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date)
    status = Column(Enum(PaymentPlanInstallmentStatus), default=PaymentPlanInstallmentStatus.SCHEDULED)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    plan = relationship("PaymentPlan", back_populates="installments")
    
    def __repr__(self):
        return f"<Installment {self.id} - ${self.amount} due {self.due_date}>"
