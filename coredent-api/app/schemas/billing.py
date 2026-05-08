"""
Billing Schemas
Pydantic models for billing validation
"""

from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class InvoiceItemCreate(BaseModel):
    """Schema for invoice line items"""
    description: str
    quantity: int = Field(default=1, gt=0)
    unit_price: Decimal = Field(gt=0)
    total: Optional[Decimal] = None
    procedure_code: Optional[str] = None

    @model_validator(mode='after')
    def calculate_total(self):
        if self.total is None:
            self.total = Decimal(str(self.quantity)) * self.unit_price
        return self


class InvoiceBase(BaseModel):
    """Base invoice schema"""
    patient_id: UUID
    subtotal: Optional[Decimal] = Field(default=None, ge=0)
    tax: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0)
    discount: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0)
    line_items: list[dict] = Field(default_factory=list)
    items: Optional[List[InvoiceItemCreate]] = None  # Typed items for API validation
    due_date: Optional[date] = None
    notes: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def map_items(cls, data):
        if isinstance(data, dict):
            # Convert InvoiceItemCreate objects to dicts for line_items
            if data.get('items') and not data.get('line_items'):
                items = data['items']
                data['line_items'] = [
                    {
                        "description": item.description if hasattr(item, 'description') else item.get('description', ''),
                        "quantity": float(item.quantity if hasattr(item, 'quantity') else item.get('quantity', 1)),
                        "unit_price": float(item.unit_price if hasattr(item, 'unit_price') else item.get('unit_price', 0)),
                        "total": float(item.total if hasattr(item, 'total') else float(item.get('quantity', 1)) * float(item.get('unit_price', 0))),
                        "procedure_code": item.procedure_code if hasattr(item, 'procedure_code') else item.get('procedure_code', None),
                    }
                    for item in (items or [])
                ]
            if data.get('line_items') and data.get('subtotal') is None:
                total = sum(
                    float(item.get('unit_price', 0)) * float(item.get('quantity', 1))
                    for item in data['line_items']
                )
                data['subtotal'] = Decimal(str(total))
            if data.get('subtotal') is None:
                data['subtotal'] = Decimal("0.00")
            if data.get('due_date'):
                if isinstance(data['due_date'], datetime):
                    data['due_date'] = data['due_date'].date()
                elif isinstance(data['due_date'], str) and 'T' in data['due_date']:
                    data['due_date'] = datetime.fromisoformat(data['due_date']).date().isoformat()
        return data


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices"""
    pass


class InvoiceResponse(InvoiceBase):
    """Schema for invoice responses"""
    id: UUID
    invoice_number: str
    total: Decimal
    total_amount: Optional[Decimal] = None  # Alias for test compatibility
    amount: Optional[Decimal] = None  # Alias for test compatibility
    amount_paid: Decimal
    balance_due: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    @model_validator(mode='after')
    def set_aliases(self):
        if self.total_amount is None:
            self.total_amount = self.total
        if self.amount is None:
            self.amount = self.total
        return self

    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: lambda v: str(v) if v is not None else None})


class PaymentBase(BaseModel):
    """Base payment schema"""
    patient_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    amount: Decimal = Field(gt=0)
    payment_method: str
    payment_date: datetime
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Schema for creating payments"""
    pass


class PaymentResponse(PaymentBase):
    """Schema for payment responses"""
    id: UUID
    payment_number: str
    status: str
    refunded_at: Optional[datetime] = None
    refunded_amount: Optional[Decimal] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: lambda v: str(v) if v is not None else None})


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices"""
    subtotal: Optional[Decimal] = Field(default=None, ge=0)
    tax: Optional[Decimal] = Field(default=None, ge=0)
    discount: Optional[Decimal] = Field(default=None, ge=0)
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list"""
    invoices: list[InvoiceResponse]
    count: int


class PaymentListResponse(BaseModel):
    """Schema for paginated payment list"""
    payments: list[PaymentResponse]
    count: int


class BillingSummary(BaseModel):
    """Schema for billing summary statistics"""
    total_invoices: int
    total_revenue: float
    total_tax: float
    total_payments: int
    total_collected: float
    outstanding_balance: float
    status_breakdown: list[dict]