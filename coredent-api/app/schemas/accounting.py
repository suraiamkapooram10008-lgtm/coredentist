"""
Accounting Integration Schemas
QuickBooks request/response models
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class QuickBooksConnectRequest(BaseModel):
    """Request to initiate QuickBooks OAuth flow"""
    pass


class QuickBooksConnectResponse(BaseModel):
    """Response with QuickBooks authorization URL"""
    auth_url: str
    message: str


class QuickBooksInvoiceSync(BaseModel):
    """Request to sync invoices to QuickBooks"""
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    invoice_ids: Optional[List[UUID]] = None


class SyncedInvoice(BaseModel):
    """Invoice that was synced"""
    id: str
    invoice_number: str
    qb_id: str


class FailedInvoice(BaseModel):
    """Invoice that failed to sync"""
    id: str
    error: str


class QuickBooksSyncResponse(BaseModel):
    """Response from QuickBooks sync"""
    synced_count: int
    failed_count: int
    synced_invoices: List[SyncedInvoice]
    failed_invoices: List[FailedInvoice]
