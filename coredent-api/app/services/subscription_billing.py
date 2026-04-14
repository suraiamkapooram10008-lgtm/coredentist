"""
Subscription Billing Service
Handles billing, dunning, and payment retry logic
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID
import stripe as stripe_lib
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
    DunningEvent,
    DunningAction,
    SubscriptionPlan,
    SubscriptionInterval,
)
from app.models.billing import Invoice, InvoiceStatus
from app.core.config_simple import settings
from app.core.email import email_service

logger = logging.getLogger(__name__)


class SubscriptionBillingService:
    """Service for subscription billing and dunning operations"""
    
    @staticmethod
    async def send_dunning_email(
        user_email: str,
        subscription_id: str,
        attempt: int,
        error: str,
    ) -> bool:
        """Send dunning notification email"""
        try:
            await email_service.send_email(
                to=user_email,
                subject=f"Payment Failed - Subscription {subscription_id[:8]} (Attempt {attempt})",
                html_content=f"""
                <html><body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #dc3545;">Payment Issue</h2>
                    <p>We were unable to process your subscription payment.</p>
                    <p><strong>Attempt:</strong> {attempt}</p>
                    <p><strong>Error:</strong> {error}</p>
                    <p>We will automatically retry on the following schedule:</p>
                    <ul>
                        <li>Day 1: Immediate retry</li>
                        <li>Day 3: Second retry</li>
                        <li>Day 7: Third retry</li>
                        <li>Day 14: Final attempt</li>
                    </ul>
                    <p>If all attempts fail, your subscription will be paused.</p>
                    <p><a href="{settings.FRONTEND_URL}/subscriptions/billing" 
                        style="background: #007bff; color: white; padding: 12px 24px; 
                        text-decoration: none; border-radius: 4px;">Update Payment Method</a></p>
                </body></html>
                """,
                text_content=f"Payment failed for subscription {subscription_id[:8]}. Attempt {attempt}. We will retry automatically.",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send dunning email: {e}")
            return False
    
    @staticmethod
    async def send_trial_expiring_email(
        user_email: str,
        subscription_id: str,
        trial_end: datetime,
    ) -> bool:
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
                    <p><a href="{settings.FRONTEND_URL}/subscriptions/plans" 
                        style="background: #28a745; color: white; padding: 12px 24px; 
                        text-decoration: none; border-radius: 4px;">Choose a Plan</a></p>
                </body></html>
                """,
                text_content=f"Your CoreDent trial ends on {trial_end.strftime('%B %d, %Y')}. Choose a plan to continue.",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send trial expiry email: {e}")
            return False
    
    @staticmethod
    async def send_payment_receipt(
        user_email: str,
        invoice_number: str,
        amount: Decimal,
        subscription_id: str,
    ) -> bool:
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
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Invoice:</strong></td>
                            <td style="padding: 8px; border: 1px solid #ddd;">{invoice_number}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Amount:</strong></td>
                            <td style="padding: 8px; border: 1px solid #ddd;">${amount:.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border: 1px solid #ddd;"><strong>Subscription:</strong></td>
                            <td style="padding: 8px; border: 1px solid #ddd;">{subscription_id[:8]}</td>
                        </tr>
                    </table>
                    <p style="margin-top: 20px;">Download your full invoice from your account.</p>
                </body></html>
                """,
                text_content=f"Payment receipt: Invoice {invoice_number}, Amount ${amount:.2f}",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send receipt email: {e}")
            return False
    
    @staticmethod
    async def process_dunning(
        db: AsyncSession,
        background_tasks: Any,
    ) -> Dict[str, int]:
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
        failed_count = 0
        
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
                        invoices = stripe_lib.Invoice.list(
                            subscription=sub.stripe_subscription_id,
                            status="open",
                            limit=1
                        )
                        
                        if invoices and invoices.data:
                            invoice = invoices.data[0]
                            stripe_lib.Invoice.finalize_invoice(invoice.id)
                            dunning_event.result = "success"
                            dunning_event.executed_at = now
                            sub.status = SubscriptionStatus.ACTIVE
                            sub.dunning_retry_count = 0
                            sub.last_payment_error = None
                            processed_count += 1
                            await db.commit()
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
                            
                            # Send dunning email in background
                            if sub.user:
                                background_tasks.add_task(
                                    SubscriptionBillingService.send_dunning_email,
                                    sub.user.email,
                                    str(sub.id),
                                    sub.dunning_retry_count,
                                    error_msg
                                )
                        else:
                            sub.status = SubscriptionStatus.UNPAID
                            dunning_event.action = DunningAction.CANCEL_SUBSCRIPTION
                            dunning_event.result = "cancelled"
                        
                        failed_count += 1
                
                await db.commit()
            
            except Exception as e:
                logger.error(f"Dunning process error for {sub.id}: {e}")
                await db.rollback()
                failed_count += 1
        
        return {
            "processed": processed_count,
            "failed": failed_count,
            "total": len(subs)
        }
    
    @staticmethod
    async def calculate_mrr(
        db: AsyncSession,
        practice_id: UUID,
    ) -> Decimal:
        """Calculate Monthly Recurring Revenue"""
        result = await db.execute(
            select(Subscription).where(
                Subscription.practice_id == practice_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
            )
        )
        active_subs = result.scalars().all()
        
        mrr = Decimal(0)
        for sub in active_subs:
            if sub.plan:
                if sub.plan.interval == SubscriptionInterval.MONTHLY:
                    mrr += sub.plan.amount
                elif sub.plan.interval == SubscriptionInterval.ANNUAL:
                    mrr += sub.plan.amount / 12
                elif sub.plan.interval == SubscriptionInterval.QUARTERLY:
                    mrr += sub.plan.amount / 3
                elif sub.plan.interval == SubscriptionInterval.SEMI_ANNUAL:
                    mrr += sub.plan.amount / 6
                elif sub.plan.interval == SubscriptionInterval.WEEKLY:
                    mrr += sub.plan.amount * Decimal("4.33")
        
        return mrr
    
    @staticmethod
    async def calculate_churn_rate(
        db: AsyncSession,
        practice_id: UUID,
    ) -> float:
        """Calculate monthly churn rate"""
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Count active subscriptions
        active_result = await db.execute(
            select(func.count(Subscription.id)).where(
                Subscription.practice_id == practice_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
            )
        )
        total_active = active_result.scalar() or 0
        
        # Count canceled this month
        canceled_result = await db.execute(
            select(func.count(Subscription.id)).where(
                Subscription.practice_id == practice_id,
                Subscription.status == SubscriptionStatus.CANCELED,
                Subscription.canceled_at >= month_start,
            )
        )
        total_canceled = canceled_result.scalar() or 0
        
        if total_active + total_canceled == 0:
            return 0.0
        
        return (total_canceled / (total_active + total_canceled)) * 100
    
    @staticmethod
    async def calculate_average_lifetime(
        db: AsyncSession,
        practice_id: UUID,
    ) -> float:
        """Calculate average subscription lifetime in days"""
        now = datetime.now(timezone.utc)
        
        result = await db.execute(
            select(Subscription.created_at).where(
                Subscription.practice_id == practice_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
            )
        )
        created_dates = result.scalars().all()
        
        if not created_dates:
            return 0.0
        
        total_days = sum((now - cd).total_seconds() / 86400 for cd in created_dates)
        return total_days / len(created_dates)
    
    @staticmethod
    async def get_subscription_stats(
        db: AsyncSession,
        practice_id: UUID,
    ) -> Dict[str, Any]:
        """Get comprehensive subscription statistics"""
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
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
        
        # Calculate metrics
        mrr = await SubscriptionBillingService.calculate_mrr(db, practice_id)
        churn_rate = await SubscriptionBillingService.calculate_churn_rate(db, practice_id)
        avg_lifetime = await SubscriptionBillingService.calculate_average_lifetime(db, practice_id)
        
        return {
            "total_active": status_counts.get("active", 0),
            "total_trials": status_counts.get("trialing", 0),
            "total_past_due": status_counts.get("past_due", 0),
            "total_canceled_this_month": status_counts.get("canceled", 0),
            "mrr": float(mrr),
            "churn_rate": round(churn_rate, 2),
            "average_lifetime_days": round(avg_lifetime, 1),
        }
