"""
Inventory Schemas
Pydantic models for inventory management, vendors, rules, and contracts.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID

# --- Inventory Items ---
class InventoryItemBase(BaseModel):
    name: str
    sku: Optional[str] = None
    category: Optional[str] = None
    current_quantity: float = 0.0

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemResponse(InventoryItemBase):
    id: UUID
    practice_id: UUID
    class Config:
        from_attributes = True


# --- Supplier / Vendor ---
class SupplierBase(BaseModel):
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    account_number: Optional[str] = None
    payment_terms: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: UUID
    practice_id: UUID
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# --- Vendor Contracts ---
class VendorContractBase(BaseModel):
    supplier_id: UUID
    contract_number: Optional[str] = None
    start_date: datetime
    end_date: datetime
    discount_percentage: Optional[float] = None
    minimum_order_value: Optional[float] = None
    shipping_terms: Optional[str] = None
    document_url: Optional[str] = None
    notes: Optional[str] = None

class VendorContractCreate(VendorContractBase):
    pass

class VendorContractResponse(VendorContractBase):
    id: UUID
    practice_id: UUID
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

# --- Reorder Rules ---
class ReorderRuleBase(BaseModel):
    item_id: UUID
    supplier_id: Optional[UUID] = None
    trigger_quantity: int = Field(..., ge=0)
    reorder_quantity: int = Field(..., gt=0)
    auto_approve: bool = False
    is_active: bool = True

class ReorderRuleCreate(ReorderRuleBase):
    pass

class ReorderRuleResponse(ReorderRuleBase):
    id: UUID
    practice_id: UUID
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

# --- Vendor Invoices ---
class VendorInvoiceBase(BaseModel):
    supplier_id: UUID
    purchase_order_id: Optional[UUID] = None
    invoice_number: str
    invoice_date: datetime
    due_date: datetime
    amount_due: float = Field(..., ge=0)
    amount_paid: float = 0
    status: str = "unpaid"
    notes: Optional[str] = None

class VendorInvoiceCreate(VendorInvoiceBase):
    pass

class VendorInvoiceResponse(VendorInvoiceBase):
    id: UUID
    practice_id: UUID
    payment_date: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

# --- Check Response ---
class ReorderCheckResponse(BaseModel):
    alerts_created: int
    purchase_orders_created: int
    items_processed: List[str]

class SupplierListResponse(BaseModel):
    suppliers: List[SupplierResponse]
    count: int
