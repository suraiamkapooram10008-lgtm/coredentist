"""
Settings Endpoints
Practice and billing settings management
"""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.models.practice import Practice
from app.schemas.settings import BillingPreferencesResponse, BillingPreferencesUpdate

router = APIRouter()


@router.get("/billing", response_model=BillingPreferencesResponse)
async def get_billing_preferences(
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> BillingPreferencesResponse:
    """
    Get billing preferences for the practice
    """
    # Get practice
    stmt = select(Practice).where(Practice.id == current_user.practice_id)
    result = await db.execute(stmt)
    practice = result.scalar_one_or_none()

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
) -> BillingPreferencesResponse:
    """
    Update billing preferences for the practice
    """
    # Get practice
    stmt = select(Practice).where(Practice.id == current_user.practice_id)
    result = await db.execute(stmt)
    practice = result.scalar_one_or_none()

    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")

    # Update fields (map camelCase schema to snake_case model)
    field_map = {
        "taxRate": "tax_rate",
        "currency": "currency",
        "invoicePrefix": "invoice_prefix",
        "paymentTerms": "payment_terms",
        "lateFeePercentage": "late_fee_percentage",
        "acceptedPaymentMethods": "accepted_payment_methods",
        "autoSendInvoices": "auto_send_invoices",
        "autoSendReminders": "auto_send_reminders",
        "reminderDaysBefore": "reminder_days_before",
    }
    update_data = preferences.model_dump(exclude_unset=True)
    for schema_field, value in update_data.items():
        model_field = field_map.get(schema_field, schema_field)
        if hasattr(practice, model_field):
            setattr(practice, model_field, value)

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
