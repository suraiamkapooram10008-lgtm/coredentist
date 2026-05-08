"""
Payroll & Commission Models
Employee compensation, time tracking, commission structures, production tracking, and PTO management.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Integer, Boolean, Date, Numeric, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.base import Base


# ============================================
# ENUMS
# ============================================

class PayType(str, enum.Enum):
    SALARY = "salary"
    HOURLY = "hourly"
    CONTRACT = "contract"


class CommissionType(str, enum.Enum):
    PRODUCTION_PERCENTAGE = "production_percentage"
    COLLECTION_PERCENTAGE = "collection_percentage"
    PER_PROCEDURE = "per_procedure"
    TIERED = "tiered"


class TimesheetStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PayrollPeriodStatus(str, enum.Enum):
    OPEN = "open"
    PROCESSING = "processing"
    CLOSED = "closed"


class PTOType(str, enum.Enum):
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    HOLIDAY = "holiday"
    UNPAID = "unpaid"


class PTORequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


# ============================================
# MODELS
# ============================================

class EmployeeCompensation(Base):
    """Employee compensation structure — salary, hourly rate, and commission config"""
    __tablename__ = "employee_compensation"

    __table_args__ = (
        Index('idx_emp_comp_user', 'user_id'),
        Index('idx_emp_comp_practice', 'practice_id'),
        Index('idx_emp_comp_active', 'is_active'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)

    # Pay structure
    pay_type = Column(Enum(PayType), nullable=False, default=PayType.HOURLY)
    pay_rate = Column(Numeric(10, 2), nullable=False)  # Annual salary or hourly rate
    overtime_rate_multiplier = Column(Numeric(4, 2), default=1.5)
    overtime_threshold_hours = Column(Numeric(5, 2), default=40)  # Weekly hours before OT

    # Commission
    commission_enabled = Column(Boolean, default=False)
    commission_structure_id = Column(UUID(as_uuid=True), ForeignKey("commission_structures.id"))

    # Effective dates
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date)  # NULL = currently active

    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User")
    practice = relationship("Practice")
    commission_structure = relationship("CommissionStructure")

    def __repr__(self):
        return f"<EmployeeCompensation {self.user_id} - {self.pay_type} ${self.pay_rate}>"


class CommissionStructure(Base):
    """Commission calculation rules"""
    __tablename__ = "commission_structures"

    __table_args__ = (
        Index('idx_commission_practice', 'practice_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    commission_type = Column(Enum(CommissionType), nullable=False)

    # Simple percentage rate
    rate_percentage = Column(Numeric(5, 2))  # e.g., 30.00 = 30%

    # Tiered rates (for TIERED type)
    # Format: [{"min": 0, "max": 10000, "rate": 25}, {"min": 10001, "max": 20000, "rate": 30}, ...]
    tiers = Column(JSON, default=list)

    # Per-procedure rates (for PER_PROCEDURE type)
    # Format: {"D2150": 50.00, "D2391": 75.00, ...}
    procedure_rates = Column(JSON, default=dict)

    # Applies to specific roles
    applies_to_roles = Column(JSON, default=list)  # ["dentist", "hygienist"]

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    practice = relationship("Practice")

    def __repr__(self):
        return f"<CommissionStructure {self.name} ({self.commission_type})>"


class Timesheet(Base):
    """Employee time tracking records"""
    __tablename__ = "timesheets"

    __table_args__ = (
        Index('idx_timesheet_user', 'user_id'),
        Index('idx_timesheet_practice', 'practice_id'),
        Index('idx_timesheet_date', 'work_date'),
        Index('idx_timesheet_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)

    work_date = Column(Date, nullable=False)
    clock_in = Column(DateTime(timezone=True), nullable=False)
    clock_out = Column(DateTime(timezone=True))
    break_minutes = Column(Integer, default=0)
    total_hours = Column(Numeric(5, 2))  # Computed on clock-out
    overtime_hours = Column(Numeric(5, 2), default=0)

    status = Column(Enum(TimesheetStatus), default=TimesheetStatus.PENDING)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)

    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    practice = relationship("Practice")
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<Timesheet {self.user_id} {self.work_date} - {self.total_hours}h>"


class PayrollPeriod(Base):
    """Payroll run periods"""
    __tablename__ = "payroll_periods"

    __table_args__ = (
        Index('idx_payroll_period_practice', 'practice_id'),
        Index('idx_payroll_period_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    pay_date = Column(Date)

    status = Column(Enum(PayrollPeriodStatus), default=PayrollPeriodStatus.OPEN)

    total_gross = Column(Numeric(12, 2), default=0)
    total_commissions = Column(Numeric(12, 2), default=0)
    total_overtime = Column(Numeric(12, 2), default=0)
    total_bonuses = Column(Numeric(12, 2), default=0)
    total_deductions = Column(Numeric(12, 2), default=0)

    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    processed_at = Column(DateTime(timezone=True))
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    practice = relationship("Practice")
    processor = relationship("User", foreign_keys=[processed_by])
    entries = relationship("PayrollEntry", back_populates="payroll_period", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PayrollPeriod {self.period_start} to {self.period_end} ({self.status})>"


class PayrollEntry(Base):
    """Individual employee payroll entry for a period"""
    __tablename__ = "payroll_entries"

    __table_args__ = (
        Index('idx_payroll_entry_period', 'payroll_period_id'),
        Index('idx_payroll_entry_user', 'user_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_period_id = Column(UUID(as_uuid=True), ForeignKey("payroll_periods.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Hours
    regular_hours = Column(Numeric(6, 2), default=0)
    overtime_hours = Column(Numeric(6, 2), default=0)

    # Pay breakdown
    base_pay = Column(Numeric(10, 2), default=0)
    overtime_pay = Column(Numeric(10, 2), default=0)
    commission_amount = Column(Numeric(10, 2), default=0)
    bonus = Column(Numeric(10, 2), default=0)

    # Deductions (stored as JSON for flexibility)
    deductions = Column(JSON, default=dict)  # {"insurance": 250, "retirement": 150, ...}
    total_deductions = Column(Numeric(10, 2), default=0)

    # Totals
    gross_pay = Column(Numeric(10, 2), default=0)
    net_pay = Column(Numeric(10, 2), default=0)

    # Production metrics for this period
    total_production = Column(Numeric(12, 2), default=0)
    total_collections = Column(Numeric(12, 2), default=0)
    procedures_completed = Column(Integer, default=0)

    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    payroll_period = relationship("PayrollPeriod", back_populates="entries")
    user = relationship("User")

    def __repr__(self):
        return f"<PayrollEntry {self.user_id} - Gross: ${self.gross_pay}>"


class ProductionLog(Base):
    """Provider production tracking — auto-logged from completed procedures"""
    __tablename__ = "production_logs"

    __table_args__ = (
        Index('idx_production_user', 'user_id'),
        Index('idx_production_practice', 'practice_id'),
        Index('idx_production_date', 'service_date'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"))

    # Procedure info
    procedure_code = Column(String(20))
    procedure_name = Column(String(255))
    tooth_number = Column(String(10))

    # Financials
    production_amount = Column(Numeric(10, 2), nullable=False)  # Fee charged
    collection_amount = Column(Numeric(10, 2), default=0)       # Amount collected
    adjustment_amount = Column(Numeric(10, 2), default=0)       # Insurance adjustments
    write_off_amount = Column(Numeric(10, 2), default=0)

    service_date = Column(Date, nullable=False)
    is_collected = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    practice = relationship("Practice")
    patient = relationship("Patient")

    def __repr__(self):
        return f"<ProductionLog {self.procedure_code} ${self.production_amount}>"


class PTOBalance(Base):
    """Employee PTO/leave balance tracking"""
    __tablename__ = "pto_balances"

    __table_args__ = (
        Index('idx_pto_balance_user', 'user_id'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)

    pto_type = Column(Enum(PTOType), nullable=False)
    year = Column(Integer, nullable=False)

    balance_hours = Column(Numeric(6, 2), default=0)
    used_hours = Column(Numeric(6, 2), default=0)
    accrual_rate_per_period = Column(Numeric(6, 2), default=0)  # Hours accrued per pay period
    max_carryover_hours = Column(Numeric(6, 2), default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    practice = relationship("Practice")

    def __repr__(self):
        return f"<PTOBalance {self.pto_type} {self.balance_hours}h>"


class PTORequest(Base):
    """Employee PTO/leave requests"""
    __tablename__ = "pto_requests"

    __table_args__ = (
        Index('idx_pto_request_user', 'user_id'),
        Index('idx_pto_request_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("practices.id"), nullable=False)

    pto_type = Column(Enum(PTOType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    hours_requested = Column(Numeric(6, 2), nullable=False)

    status = Column(Enum(PTORequestStatus), default=PTORequestStatus.PENDING)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)

    reason = Column(Text)
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    practice = relationship("Practice")
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<PTORequest {self.pto_type} {self.start_date} - {self.end_date} ({self.status})>"
