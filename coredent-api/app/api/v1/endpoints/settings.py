"""
Settings Endpoints
Practice and billing settings management
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.practice import Practice
from app.schemas.settings import BillingPreferencesResponse, BillingPreferencesUpdate

router = APIRouter()


@router.get("/billing", response_model=BillingPreferencesResponse)
async def get_billing_preferences(
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get billing preferences for the practice
    """
    from sqlalchemy import cast, String
    
    print(f"[DEBUG] User practice_id: {current_user.practice_id}")
    print(f"[DEBUG] User practice_id type: {type(current_user.practice_id)}")
    
    # Get practice - cast UUID to string for SQLite compatibility
    stmt = select(Practice).where(cast(Practice.id, String) == str(current_user.practice_id))
    print(f"[DEBUG] Query: {stmt}")
    result = await db.execute(stmt)
    practice = result.scalar_one_or_none()
    
    print(f"[DEBUG] Practice found: {practice}")
    
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")
    
    # Return billing preferences with defaults
    return {
        "taxRate": practice.tax_rate or 0.0,
        "currency": practice.currency or "USD",
        "invoicePrefix": practice.invoice_prefix or "INV",
        "paymentTerms": practice.payment_terms or 30,
        "lateFeePercentage": practice.late_fee_percentage or 0.0,
        "acceptedPaymentMethods": practice.accepted_payment_methods or ["cash", "card", "check"],
        "autoSendInvoices": practice.auto_send_invoices or False,
        "autoSendReminders": practice.auto_send_reminders or False,
        "reminderDaysBefore": practice.reminder_days_before or 3,
    }


@router.put("/billing", response_model=BillingPreferencesResponse)
async def update_billing_preferences(
    preferences: BillingPreferencesUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update billing preferences for the practice
    """
    # Get practice
    stmt = select(Practice).where(Practice.id == current_user.practice_id)
    result = await db.execute(stmt)
    practice = result.scalar_one_or_none()
    
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")
    
    # Update fields
    update_data = preferences.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(practice, field):
            setattr(practice, field, value)
    
    await db.commit()
    await db.refresh(practice)
    
    return {
        "taxRate": practice.tax_rate or 0.0,
        "currency": practice.currency or "USD",
        "invoicePrefix": practice.invoice_prefix or "INV",
        "paymentTerms": practice.payment_terms or 30,
        "lateFeePercentage": practice.late_fee_percentage or 0.0,
        "acceptedPaymentMethods": practice.accepted_payment_methods or ["cash", "card", "check"],
        "autoSendInvoices": practice.auto_send_invoices or False,
        "autoSendReminders": practice.auto_send_reminders or False,
        "reminderDaysBefore": practice.reminder_days_before or 3,
    }
