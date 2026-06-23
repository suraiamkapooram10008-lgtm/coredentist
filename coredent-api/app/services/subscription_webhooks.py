"""
Subscription Webhook Handler
Processes Stripe webhook events for subscriptions

SECURITY FIX (P0): Replaced in-process ``deque`` idempotency with
Redis-backed deduplication.  The old approach used
``_processed_events = deque(maxlen=1000)`` which is process-local.
With multiple workers/replicas, the same Stripe event delivered to
worker A was not visible to worker B, allowing duplicate processing.
``handle_invoice_failed`` previously incremented ``dunning_retry_count``
on every delivery, so a retried webhook could inflate the counter and
trigger premature dunning escalation.

Now: Redis ``SET event_id EX 86400 NX`` is used for cross-worker dedup.
If Redis is unavailable, we fall back to the in-process deque (dev only;
Redis is a hard requirement in production per config_simple.py).
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from collections import deque

from app.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    SubscriptionInterval,
)
from app.models.practice import Practice
from app.core.config_simple import settings

logger = logging.getLogger(__name__)


def _redis_client():
    """Return a Redis client if REDIS_URL is configured, else None."""
    if not settings.REDIS_URL:
        return None
    try:
        import redis as redis_lib
        return redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


class SubscriptionWebhookHandler:
    """Handler for Stripe subscription webhooks"""
    # Fallback for when Redis is unavailable (dev environments).
    # In production, Redis SETNX is used instead (cross-worker safe).
    _processed_events_fallback = deque(maxlen=1000)

    @staticmethod
    def _is_duplicate_event(event_id: str) -> bool:
        """Check if this event was already processed (cross-worker safe).

        Uses Redis ``SET event_id EX 86400 NX`` for atomic, cross-worker
        idempotency.  Falls back to in-process deque when Redis is not
        configured (development only).

        Returns True if the event was already processed.
        """
        if not event_id:
            return False

        r = _redis_client()
        if r:
            try:
                # SET NX: only sets if key does not exist.
                # Returns True if the key was set (new event), None if
                # it already existed (duplicate).
                result = r.set(
                    f"webhook:processed:{event_id}",
                    "1",
                    ex=86400,  # 24 hours
                    nx=True,
                )
                return result is None  # None = key already existed = duplicate
            except Exception as e:
                logger.warning(f"Redis dedup failed, falling back to in-process: {e}")

        # Fallback: in-process deque (dev only)
        if event_id in SubscriptionWebhookHandler._processed_events_fallback:
            return True
        SubscriptionWebhookHandler._processed_events_fallback.append(event_id)
        return False

    @staticmethod
    async def handle_subscription_created(
        db: AsyncSession,
        sub_data: Dict[str, Any],
    ) -> None:
        """Handle new subscription created in Stripe"""
        stripe_sub_id = sub_data.get("id")

        # Check if subscription already exists
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()

        if sub:
            return

        metadata = sub_data.get("metadata", {}) or {}
        practice_id = metadata.get("practice_id")
        if not practice_id:
            logger.warning("Subscription created webhook missing practice_id metadata; skipping")
            return

        # Validate practice exists
        practice_result = await db.execute(select(Practice).where(Practice.id == practice_id))
        practice = practice_result.scalar_one_or_none()
        if not practice:
            logger.warning(f"Subscription created webhook references missing practice_id={practice_id}; skipping")
            return

        # Resolve plan from metadata or price id
        plan_id_meta = metadata.get("plan_id")

        def _get_price_id(data: Dict[str, Any]) -> Optional[str]:
            items = (data.get("items") or {}).get("data") or []
            if items:
                first = items[0] or {}
                price = first.get("price") or first.get("plan") or {}
                return price.get("id")
            return None

        price_id = _get_price_id(sub_data)
        plan = None
        if plan_id_meta:
            plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id_meta))
            plan = plan_result.scalar_one_or_none()
        elif price_id:
            plan_result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.stripe_price_id == price_id))
            plan = plan_result.scalar_one_or_none()

        if not plan:
            logger.warning(
                f"Subscription created webhook could not resolve plan (plan_id={plan_id_meta}, price_id={price_id}); skipping"
            )
            return

        # Map Stripe status to enum safely
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "trialing": SubscriptionStatus.TRIALING,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "unpaid": SubscriptionStatus.UNPAID,
            "incomplete": SubscriptionStatus.INCOMPLETE,
        }
        status = status_map.get(sub_data.get("status"), SubscriptionStatus.ACTIVE)

        # Infer interval from plan or price recurring info
        interval = plan.interval
        if not interval and price_id:
            recurring_interval = (
                ((sub_data.get("items") or {}).get("data") or [{}])[0]
            ).get("price", {})
            recur = (recurring_interval.get("recurring") or {}).get("interval")
            interval_map = {
                "week": SubscriptionInterval.WEEKLY,
                "weekly": SubscriptionInterval.WEEKLY,
                "month": SubscriptionInterval.MONTHLY,
                "monthly": SubscriptionInterval.MONTHLY,
                "quarter": SubscriptionInterval.QUARTERLY,
                "year": SubscriptionInterval.ANNUAL,
                "annual": SubscriptionInterval.ANNUAL,
            }
            interval = interval_map.get(recur, SubscriptionInterval.MONTHLY)

        sub = Subscription(
            practice_id=practice.id,
            plan_id=plan.id,
            stripe_subscription_id=stripe_sub_id,
            stripe_customer_id=sub_data.get("customer"),
            status=status,
            current_period_start=datetime.fromtimestamp(
                sub_data.get("current_period_start"), tz=timezone.utc
            ) if sub_data.get("current_period_start") else None,
            current_period_end=datetime.fromtimestamp(
                sub_data.get("current_period_end"), tz=timezone.utc
            ) if sub_data.get("current_period_end") else None,
        )
        # Optionally fill missing plan interval if available
        if interval and not plan.interval:
            plan.interval = interval

        db.add(sub)
        await db.commit()
        logger.info(f"Created subscription from webhook: {stripe_sub_id}")

    @staticmethod
    async def handle_subscription_updated(
        db: AsyncSession,
        sub_data: Dict[str, Any],
    ) -> None:
        """Handle subscription update (plan changes, cancellations)"""
        stripe_sub_id = sub_data.get("id")

        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()

        if not sub:
            logger.warning(f"Subscription not found for update: {stripe_sub_id}")
            return

        # Update status
        stripe_status = sub_data.get("status")
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "trialing": SubscriptionStatus.TRIALING,
            "unpaid": SubscriptionStatus.UNPAID,
        }

        if stripe_status in status_map:
            sub.status = status_map[stripe_status]

        sub.cancel_at_period_end = sub_data.get("cancel_at_period_end", False)

        if sub_data.get("current_period_end"):
            sub.current_period_end = datetime.fromtimestamp(
                sub_data["current_period_end"],
                tz=timezone.utc
            )

        if sub_data.get("current_period_start"):
            sub.current_period_start = datetime.fromtimestamp(
                sub_data["current_period_start"],
                tz=timezone.utc
            )

        await db.commit()
        logger.info(f"Updated subscription: {stripe_sub_id}, status: {stripe_status}")

    @staticmethod
    async def handle_subscription_deleted(
        db: AsyncSession,
        sub_data: Dict[str, Any],
    ) -> None:
        """Handle subscription cancellation/deletion"""
        stripe_sub_id = sub_data.get("id")

        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()

        if not sub:
            logger.warning(f"Subscription not found for deletion: {stripe_sub_id}")
            return

        sub.status = SubscriptionStatus.CANCELED
        sub.cancel_at_period_end = True
        sub.canceled_at = datetime.now(timezone.utc)

        await db.commit()
        logger.info(f"Deleted subscription: {stripe_sub_id}")

    @staticmethod
    async def handle_invoice_succeeded(
        db: AsyncSession,
        invoice_data: Dict[str, Any],
    ) -> Optional[Subscription]:
        """Handle successful payment"""
        sub_id = invoice_data.get("subscription")

        if not sub_id:
            return None

        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
        )
        sub = result.scalar_one_or_none()

        if not sub:
            logger.warning(f"Subscription not found for invoice success: {sub_id}")
            return None

        sub.status = SubscriptionStatus.ACTIVE
        sub.dunning_retry_count = 0
        sub.last_payment_error = None

        await db.commit()
        logger.info(f"Invoice succeeded for subscription: {sub_id}")

        return sub

    @staticmethod
    async def handle_invoice_failed(
        db: AsyncSession,
        invoice_data: Dict[str, Any],
    ) -> Optional[Subscription]:
        """Handle failed payment - trigger dunning

        SECURITY FIX: Added DB-level idempotency to prevent dunning count
        inflation from retried webhooks.  We check ``last_payment_error``
        to see if this exact failure was already recorded.
        """
        sub_id = invoice_data.get("subscription")

        if not sub_id:
            return None

        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == sub_id)
        )
        sub = result.scalar_one_or_none()

        if not sub:
            logger.warning(f"Subscription not found for invoice failure: {sub_id}")
            return None

        # Idempotency: if we already recorded this exact failure, skip.
        error_msg = invoice_data.get("last_payment_error", {}).get("message", "Payment failed")
        if sub.last_payment_error == error_msg and sub.status == SubscriptionStatus.PAST_DUE:
            logger.info(f"Invoice failure already recorded for subscription {sub_id}; skipping duplicate")
            return sub

        sub.status = SubscriptionStatus.PAST_DUE
        sub.last_payment_error = error_msg
        sub.dunning_retry_count = (sub.dunning_retry_count or 0) + 1
        sub.next_retry_at = datetime.now(timezone.utc)  # Immediate retry

        await db.commit()
        logger.warning(f"Invoice failed for subscription: {sub_id}, error: {sub.last_payment_error}")

        return sub

    @staticmethod
    async def handle_trial_will_end(
        db: AsyncSession,
        sub_data: Dict[str, Any],
    ) -> Optional[Subscription]:
        """Handle trial ending soon - send reminder"""
        stripe_sub_id = sub_data.get("id")

        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()

        if not sub:
            logger.warning(f"Subscription not found for trial end: {stripe_sub_id}")
            return None

        logger.info(f"Trial ending soon for subscription: {stripe_sub_id}")
        return sub

    @staticmethod
    async def process_webhook_event(
        db: AsyncSession,
        event: Dict[str, Any],
    ) -> bool:
        """
        Process a Stripe webhook event
        Returns: True if handled successfully
        """
        event_type = event.get("type")
        event_id = event.get("id")
        data_obj = event.get("data", {}).get("object", {})

        # SECURITY FIX: Cross-worker idempotency via Redis (P0 fix)
        if SubscriptionWebhookHandler._is_duplicate_event(event_id):
            logger.info(f"Webhook event already processed: {event_id}")
            return True

        try:
            if event_type == "customer.subscription.created":
                await SubscriptionWebhookHandler.handle_subscription_created(db, data_obj)

            elif event_type == "customer.subscription.updated":
                await SubscriptionWebhookHandler.handle_subscription_updated(db, data_obj)

            elif event_type == "customer.subscription.deleted":
                await SubscriptionWebhookHandler.handle_subscription_deleted(db, data_obj)

            elif event_type == "invoice.payment_succeeded":
                await SubscriptionWebhookHandler.handle_invoice_succeeded(db, data_obj)

            elif event_type == "invoice.payment_failed":
                await SubscriptionWebhookHandler.handle_invoice_failed(db, data_obj)

            elif event_type == "customer.subscription.trial_will_end":
                await SubscriptionWebhookHandler.handle_trial_will_end(db, data_obj)

            else:
                logger.debug(f"Unhandled webhook event type: {event_type}")
                return False

            if event_id:
                # Event was already recorded in _is_duplicate_event via
                # Redis SETNX, so we don't need to add it again here.
                pass
            return True

        except Exception as e:
            logger.error(f"Error processing webhook event {event_type}: {e}")
            return False
