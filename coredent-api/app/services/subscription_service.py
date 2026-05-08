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

    def __init__(self, db: AsyncSession):
        self.db = db

    def calculate_period_start_end(
        self,
        start_date: datetime,
        billing_cycle: SubscriptionInterval,
    ) -> Tuple[datetime, datetime]:
        """Calculate current period start and end based on interval"""
        period_start = start_date or datetime.now(timezone.utc)
        interval = billing_cycle

        if interval == SubscriptionInterval.WEEKLY:
            period_end = period_start + timedelta(days=7)

        elif interval == SubscriptionInterval.MONTHLY:
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1)

        elif interval == SubscriptionInterval.QUARTERLY:
            if period_start.month <= 9:
                period_end = period_start.replace(month=period_start.month + 3)
            else:
                period_end = period_start.replace(year=period_start.year + 1, month=period_start.month - 9)

        elif interval in (SubscriptionInterval.ANNUAL, SubscriptionInterval.YEARLY):
            period_end = period_start.replace(year=period_start.year + 1)

        else:  # semi_annual
            if period_start.month <= 6:
                period_end = period_start.replace(month=period_start.month + 6)
            else:
                period_end = period_start.replace(year=period_start.year + 1, month=period_start.month - 6)

        return period_start, period_end
    
    def calculate_proration_amount(
        self,
        old_price: Decimal,
        new_price: Decimal,
        days_remaining: int,
        total_days: int
    ) -> Decimal:
        """Calculate proration amount for plan change"""
        old_amount = old_price
        new_amount = new_price
        if total_days == 0:
            return Decimal(0)
        daily_diff = (new_amount - old_amount) / Decimal(total_days)
        return daily_diff * Decimal(days_remaining)
    
    async def create_stripe_subscription(
        self,
        practice_id: UUID,
        plan_id: UUID,
        stripe_customer_id: str,
        stripe_price_id: str,
    ) -> Subscription:
        """Create a Stripe subscription and local record"""
        # Get plan
        plan_result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if not plan:
            raise ValueError("Plan not found")

        # Create Stripe subscription
        if settings.STRIPE_API_KEY and stripe_price_id:
            try:
                sub_params = {
                    "customer": stripe_customer_id,
                    "items": [{"price": stripe_price_id}],
                    "metadata": {
                        "coredent_plan_id": str(plan_id),
                        "practice_id": str(practice_id),
                    },
                }
                stripe_sub = stripe_lib.Subscription.create(**sub_params)
                stripe_sub_id = stripe_sub.id
                status = stripe_sub.status
            except stripe_lib.error.StripeError as e:
                logger.error(f"Stripe subscription creation error: {e}")
                raise
        else:
            # Stripe not configured - generate a unique local ID
            import uuid as _uuid
            stripe_sub_id = f"local_{_uuid.uuid4().hex[:12]}"
            status = "active"
            logger.warning(f"Stripe not configured, creating local subscription {stripe_sub_id}")

        # Create local subscription record
        period_start, period_end = self.calculate_period_start_end(
            start_date=datetime.now(timezone.utc),
            billing_cycle=plan.interval,
        )

        subscription = Subscription(
            practice_id=practice_id,
            plan_id=plan_id,
            status=SubscriptionStatus(status) if status else SubscriptionStatus.ACTIVE,
            interval=plan.interval,
            current_period_start=period_start,
            current_period_end=period_end,
            stripe_subscription_id=stripe_sub_id,
            stripe_customer_id=stripe_customer_id,
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription
    
    async def get_subscription_with_plan(
        self,
        subscription_id: UUID,
    ) -> Optional[Subscription]:
        """Get subscription with related plan"""
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.id == subscription_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def change_plan(
        self,
        subscription_id: UUID,
        new_plan_id: UUID,
        stripe_price_id: Optional[str] = None,
    ) -> Subscription:
        """Change subscription plan with proration"""
        # Get subscription
        subscription = await self.get_subscription_with_plan(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")

        # Get new plan
        plan_result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == new_plan_id)
        )
        new_plan = plan_result.scalar_one_or_none()
        if not new_plan:
            raise ValueError("Plan not found")

        now = datetime.now(timezone.utc)
        # Handle naive vs aware datetimes
        if subscription.current_period_end and subscription.current_period_end.tzinfo is None:
            now = now.replace(tzinfo=None)

        # Calculate proration
        if subscription.current_period_end:
            days_remaining = int((subscription.current_period_end - now).total_seconds() / 86400)
        else:
            days_remaining = 30

        proration_amount = self.calculate_proration_amount(
            subscription.plan.amount if subscription.plan else Decimal(0),
            new_plan.amount,
            days_remaining,
            30
        )

        # Update Stripe subscription
        if settings.STRIPE_API_KEY and subscription.stripe_subscription_id and stripe_price_id:
            try:
                stripe_sub = stripe_lib.Subscription.retrieve(subscription.stripe_subscription_id)
                stripe_lib.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        "id": stripe_sub["items"]["data"][0]["id"],
                        "price": stripe_price_id,
                    }],
                    proration_behavior="create_prorations",
                )
            except stripe_lib.error.StripeError as e:
                logger.error(f"Stripe plan change error: {e}")
                raise

        # Update local subscription
        subscription.plan_id = new_plan.id
        subscription.interval = new_plan.interval
        subscription.proration_behavior = ProrationBehavior.CREATE_PRORATIONS
        subscription.proration_date = now

        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription
    
    async def record_usage(
        self,
        subscription_id: UUID,
        metric_name: str,
        quantity: Decimal,
    ) -> UsageRecord:
        """Record usage for usage-based billing"""
        # Get subscription
        sub_result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = sub_result.scalar_one_or_none()
        if not subscription:
            raise ValueError("Subscription not found")

        record = UsageRecord(
            subscription_id=subscription.id,
            quantity=quantity,
            description=metric_name,
            metric_name=metric_name,
        )
        self.db.add(record)

        # Update current usage on subscription
        subscription.current_usage = (subscription.current_usage or 0) + quantity
        if subscription.plan and subscription.plan.is_usage_based:
            if subscription.current_usage > (subscription.plan.included_usage or 0):
                subscription.current_overage = subscription.current_usage - (subscription.plan.included_usage or 0)

        await self.db.commit()
        await self.db.refresh(record)
        return record
    
    async def get_usage_records(
        self,
        subscription_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[UsageRecord]:
        """Get usage records for a subscription"""
        query = select(UsageRecord).where(UsageRecord.subscription_id == subscription_id)

        if start_date:
            query = query.where(UsageRecord.timestamp >= start_date)
        if end_date:
            query = query.where(UsageRecord.timestamp <= end_date)

        query = query.order_by(UsageRecord.timestamp)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def cancel_stripe_subscription(
        self,
        subscription_id: UUID,
        cancel_at_period_end: bool = True,
    ) -> bool:
        """Cancel Stripe subscription"""
        # Get subscription
        sub_result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = sub_result.scalar_one_or_none()
        if not subscription:
            return False

        if not settings.STRIPE_API_KEY or not subscription.stripe_subscription_id:
            return False

        try:
            if cancel_at_period_end:
                stripe_lib.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True,
                )
                subscription.cancel_at_period_end = True
            else:
                stripe_lib.Subscription.cancel(subscription.stripe_subscription_id)
                subscription.status = SubscriptionStatus.CANCELED

            await self.db.commit()
            return True
        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe cancellation error for sub {subscription_id}: {e}")
            # Update local state even if Stripe call fails
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.now(timezone.utc)
            await self.db.commit()
            return False
    
    async def pause_stripe_subscription(self, subscription_id: UUID) -> bool:
        """Pause Stripe subscription"""
        sub_result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = sub_result.scalar_one_or_none()
        if not subscription:
            return False

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

    async def resume_stripe_subscription(self, subscription_id: UUID) -> bool:
        """Resume paused Stripe subscription"""
        sub_result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = sub_result.scalar_one_or_none()
        if not subscription:
            return False

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
