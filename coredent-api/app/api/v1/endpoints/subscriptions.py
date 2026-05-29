"""
Subscription Endpoints (Refactored)
Uses service layer for business logic
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, Any, List
from datetime import datetime, timedelta, timezone
from uuid import UUID
import logging

from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.config_simple import settings
from app.api.deps import get_current_user, require_role, verify_csrf
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
from app.models.subscription import (
    SubscriptionPlan,
    Subscription,
    SubscriptionStatus,
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
    SubscriptionProratePreview,
    UsageRecordCreate,
    UsageRecordResponse,
    UsageResponse,
    DunningEventList,
    SubscriptionStats,
    TrialResponse,
)
from app.schemas.common import APIResponse

# Import services
from app.services.subscription_service import SubscriptionService
from app.services.subscription_billing import SubscriptionBillingService
from app.services.subscription_webhooks import SubscriptionWebhookHandler

logger = logging.getLogger(__name__)
router = APIRouter()

# ======================= Subscription Plan Endpoints =======================

@router.get("/plans", response_model=SubscriptionPlanList)
async def list_subscription_plans(
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionPlanList:
    """List all available subscription plans"""
    query = select(SubscriptionPlan).where(SubscriptionPlan.practice_id.is_(None))
    
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
) -> SubscriptionPlanResponse:
    """Create a new subscription plan (Owner/Admin only)"""
    # Create Stripe Price if configured
    if settings.STRIPE_API_KEY and not plan_data.stripe_price_id:
        try:
            import stripe as stripe_lib
            stripe_lib.api_key = settings.STRIPE_API_KEY
            
            # Create product
            product = stripe_lib.Product.create(
                name=plan_data.name,
                description=plan_data.description,
                metadata={"coredent_plan": "true"},
            )
            
            # Create price
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
                unit_amount=int(plan_data.amount * 100),
                currency=plan_data.currency.lower(),
                recurring={
                    "interval": interval_map.get(plan_data.interval, "month"),
                    "interval_count": interval_count.get(plan_data.interval, 1),
                },
            )
            
            plan_data.stripe_price_id = price.id
            plan_data.stripe_product_id = product.id
        
        except (ValueError, TypeError) as e:
            logger.error(f"Stripe error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe error: {str(e)}")
    
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
) -> SubscriptionPlanResponse:
    """Update an existing subscription plan"""
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    
    update_data = plan_data.model_dump(exclude_unset=True)
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
) -> SubscriptionPlanResponse:
    """Get a specific subscription plan"""
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
) -> SubscriptionList:
    """List all subscriptions for the practice"""
    query = select(Subscription).where(Subscription.practice_id == current_user.practice_id)
    
    if status_filter:
        try:
            status_enum = SubscriptionStatus(status_filter)
            query = query.where(Subscription.status == status_enum)
        except ValueError:
            pass
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    offset = (page - 1) * limit
    query = query.order_by(desc(Subscription.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    subscriptions = result.scalars().all()
    
    return SubscriptionList(subscriptions=subscriptions, total=total, page=page, limit=limit)


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(
    request: Request,
    sub_data: SubscriptionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> SubscriptionResponse:
    """Create a new subscription with trial support"""
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
            detail="An active subscription already exists"
        )
    
    # Create Stripe subscription using service
    try:
        stripe_sub_id, stripe_cust_id = await SubscriptionService.create_stripe_subscription(
            db,
            plan,
            current_user.email,
            current_user.full_name,
            current_user.practice_id,
            current_user.id,
            sub_data.payment_card_id,
            sub_data.trial_period_days or plan.trial_period_days,
        )
    except (ValueError, TypeError, SQLAlchemyError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    # Calculate dates using service
    now = datetime.now(timezone.utc)
    trial_days = sub_data.trial_period_days or plan.trial_period_days
    trial_end = now + timedelta(days=trial_days) if trial_days > 0 else None
    period_start, period_end = SubscriptionService.calculate_period_start_end(plan.interval, trial_end or now)
    
    # Determine status
    status_val = SubscriptionStatus.TRIALING if trial_days > 0 else SubscriptionStatus.ACTIVE
    
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
    )
    db.add(subscription)
    
    await log_audit_event(
        db, current_user, "create_subscription", "subscription", subscription.id, request,
        {"plan_id": str(sub_data.plan_id), "trial_days": trial_days}
    )
    
    await db.commit()
    await db.refresh(subscription)
    
    # Send trial email in background
    if trial_end:
        background_tasks.add_task(
            SubscriptionBillingService.send_trial_expiring_email,
            current_user.email,
            str(subscription.id),
            trial_end
        )
    
    return subscription


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Get a specific subscription"""
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub


@router.get("/{subscription_id}/trial", response_model=TrialResponse)
async def get_trial_info(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrialResponse:
    """Get trial information for a subscription"""
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if not sub.trial_end:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No trial on this subscription")
    
    now = datetime.now(timezone.utc)
    days_used = int((now - sub.trial_start).total_seconds() / 86400) if sub.trial_start else 0
    days_remaining = int((sub.trial_end - now).total_seconds() / 86400) if sub.trial_end else 0
    
    return TrialResponse(
        subscription_id=sub.id,
        plan_name=sub.plan.name if sub.plan else "",
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
) -> SubscriptionResponse:
    """Cancel a subscription"""
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if sub.status in [SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED, SubscriptionStatus.UNPAID]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription already canceled")
    
    # Cancel Stripe subscription using service
    await SubscriptionService.cancel_stripe_subscription(sub, cancel_data.cancel_at_period_end)
    
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
) -> SubscriptionResponse:
    """Pause a subscription"""
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if sub.status != SubscriptionStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only pause active subscriptions")
    
    # Pause Stripe subscription using service
    await SubscriptionService.pause_stripe_subscription(sub)
    
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
) -> SubscriptionResponse:
    """Resume a paused subscription"""
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if sub.status != SubscriptionStatus.PAUSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only resume paused subscriptions")
    
    # Resume Stripe subscription using service
    await SubscriptionService.resume_stripe_subscription(sub)
    
    sub.status = SubscriptionStatus.ACTIVE
    sub.paused_at = None
    sub.paused_until = None
    
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
) -> SubscriptionResponse:
    """Change to a different subscription plan with proration"""
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == change_data.new_plan_id))
    new_plan = plan_result.scalar_one_or_none()
    if not new_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New plan not found")
    
    # Change plan using service
    try:
        proration_amount = await SubscriptionService.change_plan(
            db, sub, new_plan, change_data.proration_behavior
        )
    except (ValueError, TypeError, SQLAlchemyError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
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
) -> UsageRecordResponse:
    """Record usage for usage-based billing"""
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    if not sub.plan or not sub.plan.is_usage_based:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan is not usage-based")
    
    # Record usage using service
    record = await SubscriptionService.record_usage(
        db, sub, usage_data.quantity, usage_data.description, usage_data.metadata
    )
    
    return record


@router.get("/{subscription_id}/usage", response_model=UsageResponse)
async def get_usage(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UsageResponse:
    """Get usage details for current billing period"""
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    # Get usage records using service
    records = await SubscriptionService.get_usage_records(db, subscription_id, sub.current_period_start)
    
    return UsageResponse(
        subscription_id=subscription_id,
        period_start=sub.current_period_start or datetime.now(timezone.utc),
        period_end=sub.current_period_end or datetime.now(timezone.utc),
        records=records,
        summaries=[],
    )


@router.get("/{subscription_id}/dunning", response_model=DunningEventList)
async def get_dunning_events(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DunningEventList:
    """Get dunning events for subscription"""
    from app.models.subscription import DunningEvent
    
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
) -> DunningEventList:
    """Preview proration amount for plan change"""
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    old_plan = sub.plan
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
    
    amount = SubscriptionService.calculate_proration_amount(old_plan.amount, new_plan.amount, days_remaining, total_days)
    
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


@router.post("/dunning/process")
async def process_dunning(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> DunningEventList:
    """Run dunning process for all past-due subscriptions"""
    result = await SubscriptionBillingService.process_dunning(db, background_tasks)
    return APIResponse(success=True, data=result)


@router.get("/stats", response_model=SubscriptionStats)
async def get_subscription_stats(
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionStats:
    """Get subscription statistics for dashboard"""
    stats = await SubscriptionBillingService.get_subscription_stats(db, current_user.practice_id)
    return SubscriptionStats(**stats)


# ======================= Stripe Webhook Handler =======================

@router.post("/webhooks/stripe")
async def stripe_subscription_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionStats:
    """Handle Stripe webhooks for subscription events"""
    import stripe as stripe_lib
    
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
    
    # Process webhook using handler service
    success = await SubscriptionWebhookHandler.process_webhook_event(db, event)
    
    return APIResponse(success=success, message="Webhook processed")


@router.get("/{subscription_id}/invoice-history")
async def get_invoice_history(
    subscription_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionStats:
    """Get invoice history for a subscription from Stripe"""
    import stripe as stripe_lib
    
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    if not settings.STRIPE_API_KEY or not sub.stripe_subscription_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stripe not configured")
    
    try:
        stripe_lib.api_key = settings.STRIPE_API_KEY
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
    except (ValueError, TypeError, KeyError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe error: {str(e)}")


@router.post("/usage-billing/submit")
async def submit_usage_batch(
    usage_items: List[UsageRecordCreate],
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> SubscriptionStats:
    """Submit multiple usage records at once"""
    sub = await SubscriptionService.get_subscription_with_plan(db, subscription_id, current_user.practice_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    records_created = 0
    for usage in usage_items:
        await SubscriptionService.record_usage(
            db, sub, usage.quantity, usage.description, usage.metadata
        )
        records_created += 1
    
    return APIResponse(success=True, data={"records_created": records_created})