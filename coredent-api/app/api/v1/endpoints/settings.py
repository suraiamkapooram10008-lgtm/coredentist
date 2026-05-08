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
    stmt = select(Practice).where(cast(Practice.id, String) == str(current_user.practice_id))
    result = await db.execute(stmt)
    practice = result.scalar_one_or_none()
    
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")
    
    return _billing_preferences_response(practice)


@router.put("/billing", response_model=BillingPreferencesResponse)
async def update_billing_preferences(
    preferences: BillingPreferencesUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update billing preferences for the practice
    """
    from sqlalchemy import cast, String
    stmt = select(Practice).where(cast(Practice.id, String) == str(current_user.practice_id))
    result = await db.execute(stmt)
    practice = result.scalar_one_or_none()
    
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")
    
    settings_data = dict(practice.settings or {})
    update_data = preferences.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        settings_data[field] = value
    practice.settings = settings_data
    
    await db.commit()
    await db.refresh(practice)
    
    return _billing_preferences_response(practice)


def _billing_preferences_response(practice: Practice) -> dict:
    settings_data = practice.settings or {}
    return {
        "taxRate": settings_data.get("taxRate", 0.0),
        "currency": settings_data.get("currency", practice.currency or "USD"),
        "invoicePrefix": settings_data.get("invoicePrefix", "INV"),
        "paymentTerms": settings_data.get("paymentTerms", 30),
        "lateFeePercentage": settings_data.get("lateFeePercentage", 0.0),
        "acceptedPaymentMethods": settings_data.get("acceptedPaymentMethods", ["cash", "card", "check"]),
        "autoSendInvoices": settings_data.get("autoSendInvoices", False),
        "autoSendReminders": settings_data.get("autoSendReminders", False),
        "reminderDaysBefore": settings_data.get("reminderDaysBefore", 3),
    }
