"""
Advanced Subscription Endpoints
Features: Auto-billing, Payment Gateway Integration, Dunning Management, Proration,
Trial Periods, Cancellation Flow, Email Notifications, Usage-Based Billing
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc
from typing import Optional, Any, List
from datetime import datetime, timedelta, timezone
from uuid import UUID
from decimal import Decimal
import stripe as stripe_lib
import logging

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user, require_role, verify_csrf
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
from app.core.email import email_service
from app.models.subscription import (
    SubscriptionPlan,
    Subscription,
    SubscriptionInterval,
    SubscriptionStatus,
    ProrationBehavior,
    UsageMeter,
    UsageRecord,
    DunningEvent,
    DunningAction,
    CancellationSurvey,
)
from app.schemas.subscription import (
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    SubscriptionPlanResponse,
    SubscriptionPlanList,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionList,
    SubscriptionPause,
    SubscriptionResume,
    SubscriptionCancellation,
    SubscriptionChangePlan,
    SubscriptionUpdatePayment,
    SubscriptionProratePreview,
    UsageRecordCreate,
    UsageRecordResponse,
    UsageResponse,
    UsageSummary,
    DunningConfig,
    DunningEventResponse,
    DunningEventList,
    CancellationSurveyData,
    SubscriptionStats,
    SubscriptionRevenue,
    TrialResponse,
)
from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus
from app.models.payment import PaymentCard, RecurringBilling, RecurringBillingStatus
from app.schemas.common import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Stripe
if settings.STRIPE_API_KEY:
    stripe_lib.api_key = settings.STRIPE_API_KEY


# ======================= Helper Functions =======================

def _calculate_period_start_end(interval: SubscriptionInterval, from_date: Optional[datetime] = None):
    """Calculate current period start and end based on interval"""
    now = from_date or datetime.now(timezone.utc)
    if interval == SubscriptionInterval.WEEKLY:
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
        period_end = period_start + timedelta(days=7)
    elif interval == SubscriptionInterval.MONTHLY:
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = period_start.replace(day=28) + timedelta(days=4)
        period_end = next_month - timedelta(days=next_month.day - 1, hours=1, seconds=1)
    elif interval == SubscriptionInterval.QUARTERLY:
        quarter = (now.month - 1) // 3
        period_start = now.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        next_quarter_start = period_start.replace(month=period_start.month + 3) if period_start.month <= 9 else period_start.replace(year=period_start.year + 1, month=1)
        period_end = next_quarter_start - timedelta(seconds=1)
    elif interval == SubscriptionInterval.ANNUAL:
        period_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start.replace(year=period_start.year + 1) - timedelta(seconds=1)
    else:  # semi_annual
        half = 0 if now.month <= 6 else 6
        period_start = now.replace(month=half + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        next_start = period_start.replace(month=period_start.month + 6) if period_start.month <= 6 else period_start.replace(year=period_start.year + 1, month=1)
        period_end = next_start - timedelta(seconds=1)
    return period_start, period_end


def _calculate_proration_amount(old_amount: Decimal, new_amount: Decimal, days_remaining: int, total_days: int) -> Decimal:
    """Calculate proration amount for plan change"""
    if total_days == 0:
        return Decimal(0)
    daily_diff = (new_amount - old_amount) / Decimal(total_days)
    return daily_diff * Decimal(days_remaining)


async def _send_dunning_email(user_email: str, subscription_id: str, attempt: int, error: str):
    """Send dunning notification email"""
    try:
        await email_service.send_email(
            to=user_email,
            subject=f"Payment Failed - Subscription {subscription_id[:8]} (Attempt {attempt})",
            html_content=f"""
            <html><body style="font-family: Arial, sans-serif;">
                <h2 style="color: #dc3545;">Payment Payment Issue</h2>
                <p>We were unable to process your subscription payment.</p>
                <p><strong>Attempt:</strong> {attempt}</p>
                <p><strong>Error:</strong> {error}</p>
                <p>We will automatically retry on the following schedule:</p>
                <ul><li>Day 1: Immediate retry</li><li>Day 3: Second retry</li><li>Day 7: Third retry</li><li>Day 14: Final attempt</li></ul>
                <p>If all attempts fail, your subscription will be paused.</p>
                <p><a href="{settings.FRONTEND_URL}/subscriptions/billing" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Update Payment Method</a></p>
            </body></html>
            """,
            text_content=f"Payment failed for subscription {subscription_id[:8]}. Attempt {attempt}. We will retry automatically.",
        )
    except Exception as e:
        logger.error(f"Failed to send dunning email: {e}")


async def _send_trial_expiring_email(user_email: str, subscription_id: str, trial_end: datetime):
    """Send trial expiration warning"""
    try:
        await email_service.send_email(
            to=user_email,
            subject="Trial Ending Soon - CoreDent",
            html_content=f"""
            <html><body style="font-family: Arial, sans-serif;">
                <h2 style="color: #17a2b8;">Trial Ending Soon</h2>
                <p>Your CoreDent trial ends on <strong>{trial_end.strftime('%B %d, %Y')}</strong>.</p>
                <p>Subscribe now to continue enjoying all features:</p>
                <p><a href="{settings.FRONTEND_URL}/subscriptions/plans" style="background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Choose a Plan</a></p>
            </body></html>
            """,
            text_content=f"Your CoreDent trial ends on {trial_end.strftime('%B %d, %Y')}. Choose a plan to continue.",
        )
    except Exception as e:
        logger.error(f"Failed to send trial expiry email: {e}")


async def _send_payment_receipt(user_email: str, invoice_number: str, amount: Decimal, subscription_id: str):
    """Send payment receipt email"""
    try:
        await email_service.send_email(
            to=user_email,
            subject=f"Payment Receipt - Invoice {invoice_number}",
            html_content=f"""
            <html><body style="font-family: Arial, sans-serif;">
                <h2 style="color: #28a745;">Payment Receipt</h2>
                <p>Thank you for your payment!</p>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Invoice:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{invoice_number}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Amount:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">${amount:.2f}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Subscription:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{subscription_id[:8]}</td></tr>
                </table>
                <p style="margin-top: 20px;">Download your full invoice from your account.</p>
            </body></html>
            """,
            text_content=f"Payment receipt: Invoice {invoice_number}, Amount ${amount:.2f}",
        )
    except Exception as e:
        logger.error(f"Failed to send receipt email: {e}")


# ======================= Subscription Plan Endpoints =======================

@router.get("/plans", response_model=SubscriptionPlanList)
async def list_subscription_plans(
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all available subscription plans
    """
    query = select(SubscriptionPlan).where(SubscriptionPlan.practice_id.is_(None))  # Global plans
    
    if active_only:
        query = query.where(SubscriptionPlan.is_active == True)
    
    query = query.order_by(SubscriptionPlan.sort_order, SubscriptionPlan.amount)
    
    result = await db.execute(query)
    plans = result.scalars().all()
    
    return SubscriptionPlanList(plans=plans, total=len(plans))


@router.post("/plans", response_model=SubscriptionPlanResponse)
async def create_subscription_plan(
    plan_data: SubscriptionPlanCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new subscription plan (Owner/Admin only)
    """
    # Create Stripe Price if configured
    if settings.STRIPE_API_KEY and not plan_data.stripe_price_id:
        try:
            # Create product first if needed
            product = stripe_lib.Product.create(
                name=plan_data.name,
                description=plan_data.description,
                metadata={"coredent_plan": "true"},
            )
            
            # Create price with recurring interval
            interval_map = {
                "weekly": "week",
                "monthly": "month",
                "quarterly": "month",
                "semi_annual": "month",
                "annual": "year",
            }
            
            interval_count = {
                "weekly": 1,
                "monthly": 1,
                "quarterly": 3,
                "semi_annual": 6,
                "annual": 1,
            }
            
            price = stripe_lib.Price.create(
                product=product.id,
                unit_amount=int(plan_data.amount * 100),  # cents
                currency=plan_data.currency.lower(),
                recurring={
                    "interval": interval_map.get(plan_data.interval, "month"),
                    "interval_count": interval_count.get(plan_data.interval, 1),
                },
                metadata={
                    "coredent_plan": "true",
                    "trial_days": str(plan_data.trial_period_days or 0),
                },
            )
            
            plan_data.stripe_price_id = price.id
            plan_data.stripe_product_id = product.id
            
        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe error creating plan: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment processor error: {str(e)}",
            )
    
    plan = SubscriptionPlan(**plan_data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    
    return plan


@router.put("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def update_subscription_plan(
    plan_id: UUID,
    plan_data: SubscriptionPlanUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update an existing subscription plan
    """
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    # Update Stripe if needed
    update_data = plan_data.model_dump(exclude_unset=True)
    if settings.STRIPE_API_KEY and "stripe_price_id" not in update_data and plan.stripe_price_id:
        # Can't update a price - create a new one if amount/interval changes
        pass  # Stripe doesn't support updating prices directly
    
    for key, value in update_data.items():
        setattr(plan, key, value)
    
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(
    plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific subscription plan
    """
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    return plan


# ======================= Subscription Management Endpoints =======================

@router.get("", response_model=SubscriptionList)
async def list_subscriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all subscriptions for the practice"""
    query = select(Subscription).where(Subscription.practice_id == current_user.practice_id)
    
    if status_filter:
        try:
            status_enum = SubscriptionStatus(status_filter)
            query = query.where(Subscription.status == status_enum)
        except ValueError:
            pass
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    offset = (page - 1) * limit
    query = query.order_by(desc(Subscription.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    subscriptions = result.scalars().all()
    
    return SubscriptionList(
        subscriptions=subscriptions,
        total=total,
        page=page,
        limit=limit
    )


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(
    request: Request,
    sub_data: SubscriptionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new subscription with trial support.
    Automatically creates Stripe subscription if configured.
    """
    # Get the plan
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub_data.plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan or not plan.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found or inactive")
    
    # Check for existing active subscription
    existing = await db.execute(
        select(Subscription).where(
            Subscription.practice_id == current_user.practice_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING, SubscriptionStatus.PAST_DUE]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active subscription already exists. Please cancel or change plans instead."
        )
    
    # Create Stripe Subscription if configured
    stripe_sub_id = None
    stripe_cust_id = None
    if settings.STRIPE_API_KEY and plan.stripe_price_id:
        try:
            # Get or create Stripe customer
            if sub_data.payment_card_id:
                card_result = await db.execute(
                    select(PaymentCard).where(PaymentCard.id == sub_data.payment_card_id)
                )
                card = card_result.scalar_one_or_none()
                if card and card.processor_customer_id:
                    stripe_cust_id = card.processor_customer_id
            
            if not stripe_cust_id:
                customer = stripe_lib.Customer.create(
                    email=current_user.email,
                    name=current_user.full_name,
                    metadata={
                        "practice_id": str(current_user.practice_id),
                        "user_id": str(current_user.id),
                    },
                )
                stripe_cust_id = customer.id
            
            # Create subscription with trial
            sub_params = {
                "customer": stripe_cust_id,
                "items": [{"price": plan.stripe_price_id}],
                "metadata": {
                    "coredent_sub_id": str(sub_data.plan_id),
                    "practice_id": str(current_user.practice_id),
                },
            }
            
            trial_days = sub_data.trial_period_days or plan.trial_period_days
            if trial_days > 0:
                sub_params["trial_period_days"] = trial_days
            
            stripe_sub = stripe_lib.Subscription.create(**sub_params)
            stripe_sub_id = stripe_sub.id
            
        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe subscription error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment processor error: {str(e)}",
            )
    
    # Calculate dates
    now = datetime.now(timezone.utc)
    trial_days = sub_data.trial_period_days or plan.trial_period_days
    trial_end = now + timedelta(days=trial_days) if trial_days > 0 else None
    period_start, period_end = _calculate_period_start_end(plan.interval, trial_end or now)
    
    # Determine status
    if trial_days > 0:
        status_val = SubscriptionStatus.TRIALING
    else:
        status_val = SubscriptionStatus.ACTIVE
    
    # Create subscription
    subscription = Subscription(
        practice_id=current_user.practice_id,
        patient_id=sub_data.patient_id,
        plan_id=sub_data.plan_id,
        payment_card_id=sub_data.payment_card_id,
        status=status_val,
        interval=plan.interval,
        current_period_start=period_start,
        current_period_end=period_end,
        next_billing_date=trial_end or period_end,
        trial_start=now if trial_end else None,
        trial_end=trial_end,
        stripe_subscription_id=stripe_sub_id,
        stripe_customer_id=stripe_cust_id,
        proration_behavior=ProrationBehavior(sub_data.proration_behavior),
    )
    db.add(subscription)
    
    # Log creation
    await log_audit_event(
        db, current_user, "create_subscription", "subscription", subscription.id, request,
        {"plan_id": str(sub_data.plan_id), "trial_days": trial_days}
    )
    
    await db.commit()
    await db.refresh(subscription)
    
    # Send trial welcome email in background
    if trial_end:
        background_tasks.add_task(_send_trial_expiring_email, current_user.email, str(subscription.id), trial_end)
    
    return subscription


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get a specific subscription"""
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub


@router.get("/{subscription_id}/trial", response_model=TrialResponse)
async def get_trial_info(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get trial information for a subscription"""
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if not sub.trial_end:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trial on this subscription")
    
    now = datetime.now(timezone.utc)
    days_used = int((now - sub.trial_start).total_seconds() / 86400) if sub.trial_start else 0
    days_remaining = int((sub.trial_end - now).total_seconds() / 86400) if sub.trial_end else 0
    
    return TrialResponse(
        subscription_id=sub.id,
        plan_name="",  # Would need to join with plan
        trial_start=sub.trial_start,
        trial_end=sub.trial_end,
        days_remaining=max(0, days_remaining),
        days_used=days_used,
        used=sub.trial_used,
    )


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: UUID,
    cancel_data: SubscriptionCancellation,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Cancel a subscription.
    cancel_at_period_end=True: Access continues until period ends (recommended)
    cancel_at_period_end=False: Immediate cancellation
    """
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if sub.status in [SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED, SubscriptionStatus.UNPAID]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription already canceled")
    
    # Stripe cancellation
    if settings.STRIPE_API_KEY and sub.stripe_subscription_id:
        try:
            if cancel_data.cancel_at_period_end:
                stripe_lib.Subscription.modify(
                    sub.stripe_subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                stripe_lib.Subscription.cancel(sub.stripe_subscription_id)
        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe cancellation error: {e}")
    
    # Update local state
    sub.cancel_at_period_end = cancel_data.cancel_at_period_end
    sub.cancellation_reason = cancel_data.reason
    sub.cancellation_feedback = cancel_data.feedback
    
    if not cancel_data.cancel_at_period_end:
        sub.status = SubscriptionStatus.CANCELED
        sub.canceled_at = datetime.now(timezone.utc)
    
    await log_audit_event(
        db, current_user, "cancel_subscription", "subscription", subscription_id, request,
        {"cancel_at_period_end": cancel_data.cancel_at_period_end, "reason": cancel_data.reason}
    )
    
    await db.commit()
    await db.refresh(sub)
    return sub


@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
async def pause_subscription(
    subscription_id: UUID,
    pause_data: SubscriptionPause,
    request: Request,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Pause a subscription (Admin/Owner only)"""
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if sub.status != SubscriptionStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only pause active subscriptions")
    
    sub.status = SubscriptionStatus.PAUSED
    sub.paused_at = datetime.now(timezone.utc)
    sub.paused_until = pause_data.paused_until
    
    await db.commit()
    await db.refresh(sub)
    return sub


@router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
async def resume_subscription(
    subscription_id: UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Resume a paused subscription (Admin/Owner only)"""
    result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if sub.status != SubscriptionStatus.PAUSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only resume paused subscriptions")
    
    sub.status = SubscriptionStatus.ACTIVE
    sub.paused_at = None
    sub.paused_until = None
    
    # Update Stripe if configured
    if settings.STRIPE_API_KEY and sub.stripe_subscription_id:
        try:
            stripe_lib.Subscription.modify(
                sub.stripe_subscription_id,
                pause_collection="",  # Empty string unpause
            )
        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe resume error: {e}")
    
    await db.commit()
    await db.refresh(sub)
    return sub


@router.post("/{subscription_id}/change-plan", response_model=SubscriptionResponse)
async def change_plan(
    subscription_id: UUID,
    change_data: SubscriptionChangePlan,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Change to a different subscription plan with proration.
    Handles mid-cycle charges/credits automatically.
    """
    # Get subscription and new plan
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == change_data.new_plan_id))
    new_plan = plan_result.scalar_one_or_none()
    if not new_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New plan not found")
    
    # Calculate proration
    now = datetime.now(timezone.utc)
    if sub.current_period_end:
        days_remaining = int((sub.current_period_end - now).total_seconds() / 86400)
    else:
        days_remaining = 30
    
    proration_amount = _calculate_proration_amount(sub.plan.amount if sub.plan else Decimal(0), new_plan.amount, days_remaining, 30)
    
    # Update Stripe subscription
    if settings.STRIPE_API_KEY and sub.stripe_subscription_id and new_plan.stripe_price_id:
        try:
            stripe_lib.Subscription.modify(
                sub.stripe_subscription_id,
                items=[{
                    "id": stripe_lib.Subscription.retrieve(sub.stripe_subscription_id)["items"]["data"][0]["id"],
                    "price": new_plan.stripe_price_id,
                }],
                proration_behavior=change_data.proration_behavior,
            )
        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe plan change error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Payment processor error: {str(e)}")
    
    # Update local subscription
    sub.plan_id = new_plan.id
    sub.interval = new_plan.interval
    sub.proration_behavior = ProrationBehavior(change_data.proration_behavior)
    sub.proration_date = now
    
    await log_audit_event(
        db, current_user, "change_plan", "subscription", subscription_id, request,
        {"old_plan": str(sub.plan_id), "new_plan": str(new_plan.id), "proration": str(proration_amount)}
    )
    
    await db.commit()
    await db.refresh(sub)
    return sub


@router.post("/{subscription_id}/usage", response_model=UsageRecordResponse)
async def record_usage(
    subscription_id: UUID,
    usage_data: UsageRecordCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Record usage for usage-based billing"""
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    # Check if plan is usage-based
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan or not plan.is_usage_based:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan is not usage-based")
    
    # Create usage record
    record = UsageRecord(
        subscription_id=subscription_id,
        quantity=usage_data.quantity,
        description=usage_data.description,
        metadata=usage_data.metadata,
    )
    db.add(record)
    
    # Update current usage on subscription
    sub.current_usage = (sub.current_usage or 0) + usage_data.quantity
    if sub.current_usage > (plan.included_usage or 0):
        sub.current_overage = sub.current_usage - (plan.included_usage or 0)
    
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/{subscription_id}/usage", response_model=UsageResponse)
async def get_usage(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get usage details for current billing period"""
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    # Get usage records for current period
    if sub.current_period_start:
        records_result = await db.execute(
            select(UsageRecord)
            .where(
                UsageRecord.subscription_id == subscription_id,
                UsageRecord.timestamp >= sub.current_period_start,
            )
            .order_by(UsageRecord.timestamp)
        )
    else:
        records_result = await db.execute(
            select(UsageRecord)
            .where(UsageRecord.subscription_id == subscription_id)
            .order_by(UsageRecord.timestamp)
        )
    
    records = records_result.scalars().all()
    
    # Get plan usage info
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id))
    plan = plan_result.scalar_one_or_none()
    
    summaries = []
    if plan and plan.is_usage_based:
        overage = max(0, float(sub.current_usage or 0) - float(plan.included_usage or 0))
        summaries.append(UsageSummary(
            meter_id=plan.id,
            meter_name=plan.usage_meter_name or "Usage",
            unit_label=plan.usage_unit_label or "units",
            included_quantity=plan.included_usage or 0,
            used_quantity=sub.current_usage or 0,
            overage_quantity=Decimal(overage),
            overage_rate=plan.overage_rate or 0,
            overage_cost=Decimal(overage) * (plan.overage_rate or 0),
        ))
    
    return UsageResponse(
        subscription_id=subscription_id,
        period_start=sub.current_period_start or datetime.now(timezone.utc),
        period_end=sub.current_period_end or datetime.now(timezone.utc),
        records=records,
        summaries=summaries,
    )


@router.get("/{subscription_id}/dunning", response_model=DunningEventList)
async def get_dunning_events(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get dunning (payment retry) events for subscription"""
    result = await db.execute(
        select(DunningEvent)
        .where(DunningEvent.subscription_id == subscription_id)
        .order_by(DunningEvent.attempt_number)
    )
    events = result.scalars().all()
    return DunningEventList(events=events, total=len(events))


@router.get("/{subscription_id}/proration-preview")
async def preview_proration(
    subscription_id: UUID,
    new_plan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Preview proration amount for plan change"""
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    old_plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id))
    old_plan = old_plan_result.scalar_one_or_none()
    if not old_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current plan not found")
    
    new_plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == new_plan_id))
    new_plan = new_plan_result.scalar_one_or_none()
    if not new_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New plan not found")
    
    now = datetime.now(timezone.utc)
    if sub.current_period_end:
        days_remaining = int((sub.current_period_end - now).total_seconds() / 86400)
        total_days = int((sub.current_period_end - (sub.current_period_start or now)).total_seconds() / 86400)
    else:
        days_remaining = 30
        total_days = 30
    
    amount = _calculate_proration_amount(old_plan.amount, new_plan.amount, days_remaining, total_days)
    
    return {
        "subscription_id": str(subscription_id),
        "old_plan": {"name": old_plan.name, "amount": float(old_plan.amount)},
        "new_plan": {"name": new_plan.name, "amount": float(new_plan.amount)},
        "days_remaining": days_remaining,
        "total_days": total_days,
        "proration_amount": float(amount),
        "proration_credit": amount > 0,
        "effective_immediately": True,
    }


@router.post("/dunning/process", tags=["Subscription Dunning"])
async def process_dunning(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Run dunning process for all past-due subscriptions.
    Automated retry system: Day 0, 3, 7, 14 with email notifications.
    """
    now = datetime.now(timezone.utc)
    
    # Find subscriptions that need dunning
    result = await db.execute(
        select(Subscription).where(
            Subscription.status == SubscriptionStatus.PAST_DUE,
            Subscription.dunning_retry_count < Subscription.dunning_max_retries,
            Subscription.next_retry_at <= now,
        )
    )
    subs = result.scalars().all()
    
    processed_count = 0
    for sub in subs:
        try:
            # Create dunning event
            dunning_event = DunningEvent(
                subscription_id=sub.id,
                attempt_number=(sub.dunning_retry_count or 0) + 1,
                action=DunningAction.RETRY_PAYMENT,
                scheduled_at=now,
            )
            db.add(dunning_event)
            
            # Attempt payment retry via Stripe
            if settings.STRIPE_API_KEY and sub.stripe_subscription_id:
                try:
                    invoice = stripe_lib.Invoice.list_pending(subscription=sub.stripe_subscription_id, limit=1)
                    if invoice and invoice.data:
                        stripe_lib.Invoice.finalize_invoice(invoice.data[0].id)
                        dunning_event.result = "success"
                        dunning_event.executed_at = now
                        sub.status = SubscriptionStatus.ACTIVE
                        sub.dunning_retry_count = 0
                        sub.last_payment_error = None
                        processed_count += 1
                        continue
                except stripe_lib.error.StripeError as e:
                    error_msg = str(e)
                    dunning_event.result = "failed"
                    dunning_event.error_message = error_msg
                    dunning_event.executed_at = now
                    sub.dunning_retry_count = (sub.dunning_retry_count or 0) + 1
                    sub.last_payment_error = error_msg
                    
                    # Schedule next retry
                    retry_days = [0, 3, 7, 14]
                    retry_idx = sub.dunning_retry_count - 1
                    if retry_idx < len(retry_days):
                        sub.next_retry_at = now + timedelta(days=retry_days[retry_idx])
                        dunning_event.action = DunningAction.SEND_EMAIL
                        background_tasks.add_task(_send_dunning_email, "", str(sub.id), sub.dunning_retry_count, error_msg)
                    else:
                        sub.status = SubscriptionStatus.UNPAID
                        dunning_event.action = DunningAction.CANCEL_SUBSCRIPTION
                        dunning_event.result = "cancelled"
            
            await db.commit()
        except Exception as e:
            logger.error(f"Dunning process error for {sub.id}: {e}")
            await db.rollback()
    
    return APIResponse(success=True, data={"processed": processed_count, "total": len(subs)})


@router.get("/stats", response_model=SubscriptionStats)
async def get_subscription_stats(
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get subscription statistics for dashboard.
    Includes MRR, churn rate, trial conversion, and more.
    """
    practice_id = current_user.practice_id
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    
    # Count by status
    status_counts = {}
    for status_val in SubscriptionStatus:
        result = await db.execute(
            select(func.count(Subscription.id)).where(
                Subscription.practice_id == practice_id,
                Subscription.status == status_val,
            )
        )
        status_counts[status_val.name.lower()] = result.scalar() or 0
    
    # MRR calculation
    active_result = await db.execute(
        select(Subscription).where(
            Subscription.practice_id == practice_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
        )
    )
    active_subs = active_result.scalars().all()
    
    mrr = Decimal(0)
    for sub in active_subs:
        plan = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id))
        plan_obj = plan.scalar_one_or_none()
        if plan_obj:
            if plan_obj.interval == SubscriptionInterval.MONTHLY:
                mrr += plan_obj.amount
            elif plan_obj.interval == SubscriptionInterval.ANNUAL:
                mrr += plan_obj.amount / 12
            elif plan_obj.interval == SubscriptionInterval.QUARTERLY:
                mrr += plan_obj.amount / 3
            elif plan_obj.interval == SubscriptionInterval.SEMI_ANNUAL:
                mrr += plan_obj.amount / 6
            elif plan_obj.interval == SubscriptionInterval.WEEKLY:
                mrr += plan_obj.amount * 4.33
    
    # Canceled this month
    canceled_this_month_result = await db.execute(
        select(func.count(Subscription.id)).where(
            Subscription.practice_id == practice_id,
            Subscription.status == SubscriptionStatus.CANCELED,
            Subscription.canceled_at >= month_start,
        )
    )
    total_canceled = canceled_this_month_result.scalar() or 0
    
    # Churn rate
    total_active = status_counts.get("active", 0) + status_counts.get("trialing", 0)
    churn_rate = (total_canceled / max(total_active + total_canceled, 1)) * 100
    
    # Trial conversion rate
    trial_result = await db.execute(
        select(func.count(Subscription.id)).where(
            Subscription.practice_id == practice_id,
            Subscription.status == SubscriptionStatus.TRIALING,
        )
    )
    total_trials = trial_result.scalar() or 0
    trial_conversion = 0  # Would need historical data
    
    # Average lifetime
    lifetime_result = await db.execute(
        select(Subscription.created_at).where(
            Subscription.practice_id == practice_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
        )
    )
    created_dates = lifetime_result.scalars().all()
    if created_dates:
        total_days = sum((now - cd).total_seconds() / 86400 for cd in created_dates)
        avg_lifetime = total_days / len(created_dates)
    else:
        avg_lifetime = 0
    
    return SubscriptionStats(
        total_active=status_counts.get("active", 0),
        total_trials=total_trials,
        total_past_due=status_counts.get("past_due", 0),
        total_canceled_this_month=total_canceled,
        mrr=mrr,
        mrr_growth_percent=0,  # Would need last month data
        churn_rate=round(churn_rate, 2),
        trial_conversion_rate=trial_conversion,
        average_lifetime_days=round(avg_lifetime, 1),
    )


# ======================= Stripe Webhook Handler =======================

@router.post("/webhooks/stripe")
async def stripe_subscription_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Any:
    """Handle Stripe webhooks for subscription events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if not webhook_secret:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook not configured")
    
    try:
        event = stripe_lib.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe_lib.error.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    
    event_type = event["type"]
    data_obj = event["data"]["object"]
    
    # Handle subscription events
    if event_type == "customer.subscription.created":
        await _handle_subscription_created(db, data_obj)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(db, data_obj, background_tasks)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(db, data_obj)
    elif event_type == "invoice.payment_succeeded":
        await _handle_invoice_succeeded(db, data_obj, background_tasks)
    elif event_type == "invoice.payment_failed":
        await _handle_invoice_failed(db, data_obj, background_tasks)
    elif event_type == "trial_will_end":
        await _handle_trial_will_end(db, data_obj, background_tasks)
    
    return APIResponse(success=True, message="Webhook processed")


async def _handle_subscription_created(db: AsyncSession, sub_data: dict):
    """Handle new subscription created in Stripe"""
    stripe_sub_id = sub_data.get("id")
    result = await db.execute(select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id))
    sub = result.scalar_one_or_none()
    if not sub:
        # Create subscription from webhook data
        sub = Subscription(
            practice_id=sub_data.get("metadata", {}).get("practice_id"),
            stripe_subscription_id=stripe_sub_id,
            stripe_customer_id=sub_data.get("customer"),
            status=SubscriptionStatus(sub_data.get("status", "active")),
            current_period_start=datetime.fromtimestamp(sub_data.get("current_period_start"), tz=timezone.utc),
            current_period_end=datetime.fromtimestamp(sub_data.get("current_period_end"), tz=timezone.utc),
        )
        db.add(sub)
        await db.commit()


async def _handle_subscription_updated(db: AsyncSession, sub_data: dict, background_tasks: BackgroundTasks):
    """Handle subscription update (plan changes, cancellations)"""
    stripe_sub_id = sub_data.get("id")
    result = await db.execute(select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id))
    sub = result.scalar_one_or_none()
    if not sub:
        return
    
    # Update status
    stripe_status = sub_data.get("status")
    if stripe_status == "active":
        sub.status = SubscriptionStatus.ACTIVE
    elif stripe_status == "past_due":
        sub.status = SubscriptionStatus.PAST_DUE
    elif stripe_status == "canceled":
        sub.status = SubscriptionStatus.CANCELED
    elif stripe_status == "trialing":
        sub.status = SubscriptionStatus.TRIALING
    
    sub.cancel_at_period_end = sub_data.get("cancel_at_period_end", False)
    
    if sub_data.get("current_period_end"):
        sub.current_period_end = datetime.fromtimestamp(sub_data["current_period_end"], tz=timezone.utc)
    
    await db.commit()


async def _handle_subscription_deleted(db: AsyncSession, sub_data: dict):
    """Handle subscription cancellation/deletion"""
    stripe_sub_id = sub_data.get("id")
    result = await db.execute(select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id))
    sub = result.scalar_one_or_none()
    if not sub:
        return
    
    sub.status = SubscriptionStatus.CANCELED
    sub.cancel_at_period_end = True
    sub.canceled_at = datetime.now(timezone.utc)
    await db.commit()


async def _handle_invoice_succeeded(db: AsyncSession, invoice_data: dict, background_tasks: BackgroundTasks):
    """Handle successful payment"""
    sub_id = invoice_data.get("subscription")
    if sub_id:
        result = await db.execute(select(Subscription).where(Subscription.stripe_subscription_id == sub_id))
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = SubscriptionStatus.ACTIVE
            sub.dunning_retry_count = 0
            sub.last_payment_error = None
            await db.commit()
            
            # Send receipt email
            customer_email = invoice_data.get("customer_email")
            if customer_email:
                background_tasks.add_task(
                    _send_payment_receipt,
                    customer_email,
                    invoice_data.get("number", ""),
                    Decimal(invoice_data.get("amount_paid", 0) / 100),
                    sub_id,
                )


async def _handle_invoice_failed(db: AsyncSession, invoice_data: dict, background_tasks: BackgroundTasks):
    """Handle failed payment - trigger dunning"""
    sub_id = invoice_data.get("subscription")
    if sub_id:
        result = await db.execute(select(Subscription).where(Subscription.stripe_subscription_id == sub_id))
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = SubscriptionStatus.PAST_DUE
            sub.last_payment_error = invoice_data.get("last_payment_error", {}).get("message", "Payment failed")
            sub.dunning_retry_count = (sub.dunning_retry_count or 0) + 1
            sub.next_retry_at = datetime.now(timezone.utc)  # Immediate retry
            await db.commit()


async def _handle_trial_will_end(db: AsyncSession, sub_data: dict, background_tasks: BackgroundTasks):
    """Handle trial ending soon - send reminder"""
    # This is handled by background tasks already


@router.get("/{subscription_id}/invoice-history")
async def get_invoice_history(
    subscription_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get invoice history for a subscription from Stripe"""
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    if not settings.STRIPE_API_KEY or not sub.stripe_subscription_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stripe not configured for this subscription")
    
    try:
        invoices = stripe_lib.Invoice.list(
            subscription=sub.stripe_subscription_id,
            limit=limit,
            status="all",
        )
        return {
            "subscription_id": str(subscription_id),
            "invoices": [
                {
                    "id": inv["id"],
                    "number": inv.get("number"),
                    "amount_due": inv.get("amount_due", 0) / 100,
                    "amount_paid": inv.get("amount_paid", 0) / 100,
                    "status": inv.get("status"),
                    "created": inv.get("created"),
                    "hosted_invoice_url": inv.get("hosted_invoice_url"),
                }
                for inv in invoices.get("data", [])
            ],
        }
    except stripe_lib.error.StripeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe error: {str(e)}")


@router.post("/usage-billing/submit", tags=["Subscription Usage"])
async def submit_usage_batch(
    usage_items: List[UsageRecordCreate],
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """Submit multiple usage records at once"""
    sub_result = await db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.practice_id == current_user.practice_id,
        )
    )
    sub = sub_result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    records = []
    for usage in usage_items:
        record = UsageRecord(
            subscription_id=subscription_id,
            quantity=usage.quantity,
            description=usage.description,
            metadata=usage.metadata,
        )
        db.add(record)
        records.append(record)
        sub.current_usage = (sub.current_usage or 0) + usage.quantity
    
    await db.commit()
    return APIResponse(success=True, data={"records_created": len(records)})


