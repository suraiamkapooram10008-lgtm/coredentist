"""
Settings Schemas
Pydantic models for settings endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class BillingPreferencesResponse(BaseModel):
    """Billing preferences response"""
    taxRate: float = Field(default=0.0, ge=0, le=100)
    currency: str = Field(default="USD")
    invoicePrefix: str = Field(default="INV")
    paymentTerms: int = Field(default=30, ge=0)
    lateFeePercentage: float = Field(default=0.0, ge=0, le=100)
    acceptedPaymentMethods: List[str] = Field(default=["cash", "card", "check"])
    autoSendInvoices: bool = Field(default=False)
    autoSendReminders: bool = Field(default=False)
    reminderDaysBefore: int = Field(default=3, ge=0)


class BillingPreferencesUpdate(BaseModel):
    """Billing preferences update"""
    taxRate: Optional[float] = Field(None, ge=0, le=100)
    currency: Optional[str] = None
    invoicePrefix: Optional[str] = None
    paymentTerms: Optional[int] = Field(None, ge=0)
    lateFeePercentage: Optional[float] = Field(None, ge=0, le=100)
    acceptedPaymentMethods: Optional[List[str]] = None
    autoSendInvoices: Optional[bool] = None
    autoSendReminders: Optional[bool] = None
    reminderDaysBefore: Optional[int] = Field(None, ge=0)
