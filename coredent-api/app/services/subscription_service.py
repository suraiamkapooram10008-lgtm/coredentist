"""
Subscription Service
Core business logic for subscription management
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID
import stripe as stripe_lib
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.subscription import (
    SubscriptionPlan,
    Subscription,
    SubscriptionInterval,
    SubscriptionStatus,
    ProrationBehavior,
    UsageRecord,
)
from app.models.payment import PaymentCard
from app.core.config_simple import settings

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription management operations"""
    
    @staticmethod
    def calculate_period_start_end(
        interval: SubscriptionInterval,
        from_date: Optional[datetime] = None
    ) -> Tuple[datetime, datetime]:
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
            next_quarter_start = (
                period_start.replace(month=period_start.month + 3)
                if period_start.month <= 9
                else period_start.replace(year=period_start.year + 1, month=1)
            )
            period_end = next_quarter_start - timedelta(seconds=1)
        
        elif interval == SubscriptionInterval.ANNUAL:
            period_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start.replace(year=period_start.year + 1) - timedelta(seconds=1)
        
        else:  # semi_annual
            half = 0 if now.month <= 6 else 6
            period_start = now.replace(month=half + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            next_start = (
                period_start.replace(month=period_start.month + 6)
                if period_start.month <= 6
                else period_start.replace(year=period_start.year + 1, month=1)
            )
            period_end = next_start - timedelta(seconds=1)
        
        return period_start, period_end
    
    @staticmethod
    def calculate_proration_amount(
        old_amount: Decimal,
        new_amount: Decimal,
        days_remaining: int,
        total_days: int
    ) -> Decimal:
        """Calculate proration amount for plan change"""
        if total_days == 0:
            return Decimal(0)
        daily_diff = (new_amount - old_amount) / Decimal(total_days)
        return daily_diff * Decimal(days_remaining)
    
    @staticmethod
    async def create_stripe_subscription(
        db: AsyncSession,
        plan: SubscriptionPlan,
        user_email: str,
        user_full_name: str,
        practice_id: UUID,
        user_id: UUID,
        payment_card_id: Optional[UUID] = None,
        trial_days: int = 0,
    ) -> Tuple[str, str]:
        """
        Create a Stripe subscription
        Returns: (stripe_subscription_id, stripe_customer_id)
        """
        if not settings.STRIPE_API_KEY or not plan.stripe_price_id:
            return None, None
        
        try:
            # Get or create Stripe customer
            stripe_cust_id = None
            if payment_card_id:
                card_result = await db.execute(
                    select(PaymentCard).where(PaymentCard.id == payment_card_id)
                )
                card = card_result.scalar_one_or_none()
                if card and card.processor_customer_id:
                    stripe_cust_id = card.processor_customer_id
            
            if not stripe_cust_id:
                customer = stripe_lib.Customer.create(
                    email=user_email,
                    name=user_full_name,
                    metadata={
                        "practice_id": str(practice_id),
                        "user_id": str(user_id),
                    },
                )
                stripe_cust_id = customer.id
            
            # Create subscription with trial
            sub_params = {
                "customer": stripe_cust_id,
                "items": [{"price": plan.stripe_price_id}],
                "metadata": {
                    "coredent_plan_id": str(plan.id),
                    "practice_id": str(practice_id),
                },
            }
            
            if trial_days > 0:
                sub_params["trial_period_days"] = trial_days
            
            stripe_sub = stripe_lib.Subscription.create(**sub_params)
            return stripe_sub.id, stripe_cust_id
        
        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe subscription creation error: {e}")
            raise
    
    @staticmethod
    async def get_subscription_with_plan(
        db: AsyncSession,
        subscription_id: UUID,
        practice_id: UUID,
    ) -> Optional[Subscription]:
        """Get subscription with related plan"""
        result = await db.execute(
            select(Subscription).where(
                Subscription.id == subscription_id,
                Subscription.practice_id == practice_id,
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def change_plan(
        db: AsyncSession,
        subscription: Subscription,
        new_plan: SubscriptionPlan,
        proration_behavior: str = "create_prorations",
    ) -> Decimal:
        """
        Change subscription plan with proration
        Returns: proration_amount
        """
        now = datetime.now(timezone.utc)
        
        # Calculate proration
        if subscription.current_period_end:
            days_remaining = int((subscription.current_period_end - now).total_seconds() / 86400)
        else:
            days_remaining = 30
        
        proration_amount = SubscriptionService.calculate_proration_amount(
            subscription.plan.amount if subscription.plan else Decimal(0),
            new_plan.amount,
            days_remaining,
            30
        )
        
        # Update Stripe subscription
        if settings.STRIPE_API_KEY and subscription.stripe_subscription_id and new_plan.stripe_price_id:
            try:
                stripe_sub = stripe_lib.Subscription.retrieve(subscription.stripe_subscription_id)
                stripe_lib.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        "id": stripe_sub["items"]["data"][0]["id"],
                        "price": new_plan.stripe_price_id,
                    }],
                    proration_behavior=proration_behavior,
                )
            except stripe_lib.error.StripeError as e:
                logger.error(f"Stripe plan change error: {e}")
                raise
        
        # Update local subscription
        subscription.plan_id = new_plan.id
        subscription.interval = new_plan.interval
        subscription.proration_behavior = ProrationBehavior(proration_behavior)
        subscription.proration_date = now
        
        return proration_amount
    
    @staticmethod
    async def record_usage(
        db: AsyncSession,
        subscription: Subscription,
        quantity: Decimal,
        description: str = "",
        metadata: Optional[dict] = None,
    ) -> UsageRecord:
        """Record usage for usage-based billing"""
        record = UsageRecord(
            subscription_id=subscription.id,
            quantity=quantity,
            description=description,
            metadata=metadata or {},
        )
        db.add(record)
        
        # Update current usage on subscription
        subscription.current_usage = (subscription.current_usage or 0) + quantity
        if subscription.plan and subscription.plan.is_usage_based:
            if subscription.current_usage > (subscription.plan.included_usage or 0):
                subscription.current_overage = subscription.current_usage - (subscription.plan.included_usage or 0)
        
        await db.commit()
        await db.refresh(record)
        return record
    
    @staticmethod
    async def get_usage_records(
        db: AsyncSession,
        subscription_id: UUID,
        period_start: Optional[datetime] = None,
    ) -> List[UsageRecord]:
        """Get usage records for a subscription"""
        query = select(UsageRecord).where(UsageRecord.subscription_id == subscription_id)
        
        if period_start:
            query = query.where(UsageRecord.timestamp >= period_start)
        
        query = query.order_by(UsageRecord.timestamp)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def cancel_stripe_subscription(
        subscription: Subscription,
        cancel_at_period_end: bool = True,
    ) -> bool:
        """Cancel Stripe subscription"""
        if not settings.STRIPE_API_KEY or not subscription.stripe_subscription_id:
            return False
        
        try:
            if cancel_at_period_end:
                stripe_lib.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                stripe_lib.Subscription.cancel(subscription.stripe_subscription_id)
            return True
        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe cancellation error: {e}")
            return False
    
    @staticmethod
    async def pause_stripe_subscription(subscription: Subscription) -> bool:
        """Pause Stripe subscription"""
        if not settings.STRIPE_API_KEY or not subscription.stripe_subscription_id:
            return False
        
        try:
            stripe_lib.Subscription.modify(
                subscription.stripe_subscription_id,
                pause_collection={"behavior": "mark_uncollectible"},
            )
            return True
        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe pause error: {e}")
            return False
    
    @staticmethod
    async def resume_stripe_subscription(subscription: Subscription) -> bool:
        """Resume paused Stripe subscription"""
        if not settings.STRIPE_API_KEY or not subscription.stripe_subscription_id:
            return False
        
        try:
            stripe_lib.Subscription.modify(
                subscription.stripe_subscription_id,
                pause_collection="",  # Empty string unpauses
            )
            return True
        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe resume error: {e}")
            return False
