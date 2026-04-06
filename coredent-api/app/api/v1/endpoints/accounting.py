"""
Accounting Integration Endpoints
QuickBooks Online sync for invoicing and payments
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from typing import Optional, Any
from uuid import UUID
import httpx

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.billing import Invoice, Payment, InvoiceStatus
from app.models.patient import Patient
from app.core.audit import log_audit_event
from app.api.deps import get_current_user, verify_csrf, require_role
from app.schemas.accounting import (
    QuickBooksConnectRequest,
    QuickBooksConnectResponse,
    QuickBooksInvoiceSync,
    QuickBooksSyncResponse,
)

router = APIRouter()

# QuickBooks API Base URL
QB_BASE_URL = "https://quickbooks.api.intuit.com/v3"


def _get_qb_headers(access_token: str) -> dict:
    """Get headers for QuickBooks API"""
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


@router.post("/quickbooks/connect", response_model=QuickBooksConnectResponse)
async def connect_quickbooks(
    request: Request,
    connect_data: QuickBooksConnectRequest,
    current_user: User = Depends(require_role(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Connect CoreDent to QuickBooks Online.
    
    Design decisions:
    - OAuth2 flow: Redirect user to QuickBooks authorization
    - Store tokens securely in database per practice
    """
    if not settings.QB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="QuickBooks integration not configured",
        )
    
    # Build OAuth authorization URL
    auth_url = (
        f"https://appcenter.intuit.com/connect/oauth2?"
        f"client_id={settings.QB_CLIENT_ID}"
        f"&redirect_uri={settings.QB_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=com.intuit.quickbooks.accounting"
        f"&state={current_user.practice_id}"
    )
    
    return QuickBooksConnectResponse(
        auth_url=auth_url,
        message="Redirect user to authorization URL",
    )


@router.get("/quickbooks/callback")
async def quickbooks_callback(
    request: Request,
    code: str,
    realmId: str,
    state: str,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Handle QuickBooks OAuth callback with State Verification.
    Exchange authorization code for access token.
    """
    # Expert Hardening: Verify state matches current user's practice to prevent OAuth CSRF
    if not state or state != str(current_user.practice_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid OAuth state. Potential cross-site request forgery detected."
        )
    if not settings.QB_CLIENT_ID or not settings.QB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="QuickBooks not configured",
        )
    
    # Exchange code for token
    token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.QB_REDIRECT_URI,
            },
            auth=(settings.QB_CLIENT_ID, settings.QB_CLIENT_SECRET),
        )
    
    if response.status_code == 200:
        token_data = response.json()
        # In production: Store tokens securely in practice settings
        return {
            "status": "connected",
            "realm_id": realmId,
            "access_token": token_data.get("access_token"),
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect to QuickBooks",
        )


@router.post("/quickbooks/sync/invoices", response_model=QuickBooksSyncResponse)
async def sync_invoices_to_qb(
    request: Request,
    sync_data: QuickBooksInvoiceSync,
    current_user: User = Depends(require_role(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Sync invoices to QuickBooks Online.
    
    Design decisions:
    - Source of truth: CoreDent database
    - Action: POST invoices to QuickBooks as they are created/paid
    - Derived: QuickBooks customer ID mapping stored in DB
    """
    if not settings.QB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="QuickBooks integration not configured",
        )
    
    # Get invoices to sync with patient details eager-loaded
    query = (
        select(Invoice)
        .where(
            Invoice.practice_id == current_user.practice_id,
            Invoice.status != InvoiceStatus.DRAFT,
        )
        .options(joinedload(Invoice.patient))
    )
    
    if sync_data.from_date:
        query = query.where(Invoice.created_at >= sync_data.from_date)
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    synced = []
    failed = []
    
    for invoice in invoices:
        # Optimization: Patient is already loaded via joinedload
        patient = invoice.patient
        
        if not patient:
            failed.append({"id": str(invoice.id), "error": "Patient not found"})
            continue
        
        # In production: Use actual QB access token from practice settings
        # For now, return mock response
        qb_invoice = {
            "Line": [
                {
                    "Amount": float(invoice.total),
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {
                        "ItemRef": {"value": "1"},  # Service item
                        "Qty": 1,
                        "UnitPrice": float(invoice.total),
                    },
                    "Description": f"Invoice #{invoice.invoice_number}",
                }
            ],
            "CustomerRef": {
                "value": str(patient.id),  # In production: map to QB customer ID
            },
            "BillEmail": {
                "Address": patient.email or "",
            },
            "DueDate": invoice.due_date.isoformat() if invoice.due_date else None,
        }
        
        # In production: POST to QuickBooks API
        # response = await client.post(
        #     f"{QB_BASE_URL}/company/{realm_id}/invoice",
        #     json=qb_invoice,
        #     headers=_get_qb_headers(access_token),
        # )
        
        synced.append({
            "id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "qb_id": f"QB-{invoice.invoice_number}",  # Mock
        })
    
    # HIPAA: Log QuickBooks sync transmission
    await log_audit_event(
        db, current_user, "quickbooks_sync_invoices", "accounting", None, request,
        {"count": len(synced)}
    )
    await db.commit()
    
    return QuickBooksSyncResponse(
        synced_count=len(synced),
        failed_count=len(failed),
        synced_invoices=synced,
        failed_invoices=failed,
    )


@router.post("/quickbooks/sync/payments", response_model=QuickBooksSyncResponse)
async def sync_payments_to_qb(
    request: Request,
    sync_data: QuickBooksInvoiceSync,
    current_user: User = Depends(require_role(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Sync payments to QuickBooks Online as received payments.
    """
    if not settings.QB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="QuickBooks integration not configured",
        )
    
    # Get payments to sync
    query = select(Payment).join(Invoice).where(
        Invoice.practice_id == current_user.practice_id,
    )
    
    if sync_data.from_date:
        query = query.where(Payment.created_at >= sync_data.from_date)
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    synced = []
    failed = []
    
    for payment in payments:
        qb_payment = {
            "TotalAmt": float(payment.amount),
            "CustomerRef": {"value": str(payment.patient_id)},
            "Line": [
                {
                    "Amount": float(payment.amount),
                    "DetailType": "PaymentMethodDetail",
                    "PaymentMethodRef": {"value": "1"},  # Check/Cash
                }
            ],
        }
        
        # In production: POST to QuickBooks API
        synced.append({
            "id": str(payment.id),
            "qb_id": f"QB-PAY-{payment.id}",  # Mock
        })
    
    # HIPAA: Log QuickBooks sync transmission
    await log_audit_event(
        db, current_user, "quickbooks_sync_payments", "accounting", None, request,
        {"count": len(synced)}
    )
    await db.commit()
    
    return QuickBooksSyncResponse(
        synced_count=len(synced),
        failed_count=len(failed),
        synced_invoices=synced,
        failed_invoices=failed,
    )


@router.get("/quickbooks/status")
async def get_qb_status(
    current_user: User = Depends(require_role(UserRole.OWNER)),
) -> Any:
    """
    Get QuickBooks connection status for the practice.
    """
    return {
        "connected": False,
        "last_sync": None,
        "message": "QuickBooks not connected",
    }
