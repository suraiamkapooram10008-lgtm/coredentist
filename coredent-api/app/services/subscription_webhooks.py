"""
Subscription Webhook Handler
Processes Stripe webhook events for subscriptions
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import stripe as stripe_lib
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
)
from app.core.config_simple import settings

logger = logging.getLogger(__name__)


class SubscriptionWebhookHandler:
    """Handler for Stripe subscription webhooks"""
    
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
        
        if not sub:
            # Create subscription from webhook data
            sub = Subscription(
                practice_id=sub_data.get("metadata", {}).get("practice_id"),
                stripe_subscription_id=stripe_sub_id,
                stripe_customer_id=sub_data.get("customer"),
                status=SubscriptionStatus(sub_data.get("status", "active")),
                current_period_start=datetime.fromtimestamp(
                    sub_data.get("current_period_start"),
                    tz=timezone.utc
                ),
                current_period_end=datetime.fromtimestamp(
                    sub_data.get("current_period_end"),
                    tz=timezone.utc
                ),
            )
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
        """Handle failed payment - trigger dunning"""
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
        
        sub.status = SubscriptionStatus.PAST_DUE
        sub.last_payment_error = (
            invoice_data.get("last_payment_error", {}).get("message", "Payment failed")
        )
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
        data_obj = event.get("data", {}).get("object", {})
        
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
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing webhook event {event_type}: {e}")
            return False
