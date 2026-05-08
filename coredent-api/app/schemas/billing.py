"""
Billing Schemas
Pydantic models for billing data validation
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID
from decimal import Decimal

from app.models.billing import InvoiceStatus, PaymentMethod, PaymentStatus


# Line Item Schemas

class LineItemBase(BaseModel):
    """Base line item schema"""
    description: str
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    total: Decimal = Field(..., ge=0)
    
    @validator('total')
    def validate_total(cls, v, values):
        if 'quantity' in values and 'unit_price' in values:
            expected_total = values['quantity'] * values['unit_price']
            if v != expected_total:
                raise ValueError(f'total must equal quantity * unit_price ({expected_total})')
        return v


class LineItemCreate(LineItemBase):
    """Schema for creating line items"""
    pass


# Invoice Schemas

class InvoiceBase(BaseModel):
    """Base invoice schema"""
    patient_id: UUID
    status: Optional[InvoiceStatus] = InvoiceStatus.PENDING
    line_items: List[LineItemCreate]
    tax_rate: Optional[Decimal] = Field(Decimal('0.0'), ge=0, le=1)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices"""
    pass


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices"""
    status: Optional[InvoiceStatus] = None
    line_items: Optional[List[LineItemCreate]] = None
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice responses"""
    id: UUID
    practice_id: UUID
    invoice_number: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    created_at: datetime
    updated_at: datetime
    amount_paid: Decimal
    balance_due: Decimal
    
    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Schema for list of invoices"""
    invoices: List[InvoiceResponse]
    count: int


# Payment Schemas

class PaymentBase(BaseModel):
    """Base payment schema"""
    invoice_id: UUID
    patient_id: UUID
    amount: Decimal = Field(..., gt=0)
    payment_method: PaymentMethod
    transaction_id: Optional[str] = None
    status: Optional[PaymentStatus] = PaymentStatus.COMPLETED
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Schema for creating payments"""
    pass


class PaymentResponse(PaymentBase):
    """Schema for payment responses"""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """Schema for list of payments"""
    payments: List[PaymentResponse]
    count: int


# Summary Schemas

class StatusBreakdown(BaseModel):
    """Schema for status breakdown"""
    status: InvoiceStatus
    count: int
    amount: float


class BillingSummary(BaseModel):
    """Schema for billing summary"""
    total_invoices: int
    total_revenue: float
    total_tax: float
    total_payments: int
    total_collected: float
    outstanding_balance: float
    status_breakdown: List[StatusBreakdown]