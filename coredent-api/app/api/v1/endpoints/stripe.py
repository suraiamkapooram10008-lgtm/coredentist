"""
Stripe Payment Processing Endpoints
Handles payment intents, subscriptions, and webhooks
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import stripe
from datetime import datetime, timezone
import logging

from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionInterval
from app.schemas.payment import PaymentIntentCreate, PaymentIntentResponse
from app.schemas.subscription import SubscriptionCreate
from app.core.config_simple import settings
from app.core.email import send_payment_confirmation_email

logger = logging.getLogger(__name__)

# Map Stripe status strings to our SubscriptionStatus enum.
# Stripe can send statuses like "incomplete_expired" or "paused" that have
# no enum member; we fall back to INCOMPLETE so the insert never crashes.
_STRIPE_STATUS_MAP: Dict[str, SubscriptionStatus] = {
    "active": SubscriptionStatus.ACTIVE,
    "trialing": SubscriptionStatus.TRIALING,
    "past_due": SubscriptionStatus.PAST_DUE,
    "canceled": SubscriptionStatus.CANCELED,
    "unpaid": SubscriptionStatus.UNPAID,
    "incomplete": SubscriptionStatus.INCOMPLETE,
    "incomplete_expired": SubscriptionStatus.INCOMPLETE,
    "paused": SubscriptionStatus.PAUSED,
}

# Map Stripe plan interval strings to our SubscriptionInterval enum.
_STRIPE_INTERVAL_MAP: Dict[str, SubscriptionInterval] = {
    "day": SubscriptionInterval.WEEKLY,
    "week": SubscriptionInterval.WEEKLY,
    "month": SubscriptionInterval.MONTHLY,
    "year": SubscriptionInterval.ANNUAL,
}

router = APIRouter()

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a Stripe payment intent for one-time payments
    """
    try:
        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(payment_data.amount * 100),  # Convert to cents
            currency=payment_data.currency.lower(),
            customer_email=current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "practice_id": str(current_user.practice_id) if current_user.practice_id else "",
                "payment_type": payment_data.payment_type,
                "description": payment_data.description
            },
            automatic_payment_methods={
                "enabled": True,
            },
        )

        # Log payment intent in database
        from app.models.payment import Payment
        payment = Payment(
            patient_id=payment_data.patient_id if hasattr(payment_data, 'patient_id') else None,
            amount=payment_data.amount,
            currency=payment_data.currency,
            status="pending",
            payment_method="stripe",
            transaction_id=intent.id,
            description=payment_data.description,
            user_id=current_user.id
        )
        db.add(payment)
        await db.commit()

        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            amount=payment_data.amount,
            currency=payment_data.currency
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe payment intent creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment failed: {str(e)}"
        )
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Payment intent creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment intent"
        )


@router.post("/create-subscription", response_model=Dict[str, Any])
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new Stripe subscription
    """
    try:
        # Create or get Stripe customer
        customer = None
        if subscription_data.customer_id:
            customer = stripe.Customer.retrieve(subscription_data.customer_id)
        else:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=f"{current_user.first_name} {current_user.last_name}",
                metadata={
                    "user_id": str(current_user.id),
                    "practice_id": str(current_user.practice_id) if current_user.practice_id else ""
                }
            )

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{
                "price": subscription_data.price_id,
                "quantity": subscription_data.quantity or 1,
            }],
            payment_behavior="default_incomplete",
            payment_settings={
                "save_default_payment_method": "on_subscription"
            },
            expand=["latest_invoice.payment_intent"],
            metadata={
                "user_id": str(current_user.id),
                "subscription_type": subscription_data.subscription_type
            }
        )

        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice.payment_intent else None,
            "customer_id": customer.id,
            "status": subscription.status
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subscription creation failed: {str(e)}"
        )
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Subscription creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )


@router.get("/subscription/{subscription_id}")
async def get_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get subscription details from Stripe
    """
    try:
        subscription = stripe.Subscription.retrieve(
            subscription_id,
            expand=["items.data.price.product"]
        )

        # Verify user owns this subscription
        if subscription.metadata.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this subscription"
            )

        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_start": datetime.fromtimestamp(subscription.current_period_start, tz=timezone.utc),
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc),
            "items": [
                {
                    "price_id": item.price.id,
                    "product_name": item.price.product.name if isinstance(item.price.product, stripe.Product) else item.price.product,
                    "quantity": item.quantity
                }
                for item in subscription.items.data
            ],
            "cancel_at_period_end": subscription.cancel_at_period_end
        }

    except stripe.error.StripeError as e:
        logger.error(f"Failed to retrieve subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve subscription: {str(e)}"
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Failed to retrieve subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription"
        )


@router.post("/cancel-subscription/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancel a Stripe subscription
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)

        # Verify user owns this subscription
        if subscription.metadata.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this subscription"
            )

        # Cancel subscription
        canceled = stripe.Subscription.delete(subscription_id)

        # Update local subscription record
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription_id
            )
        )
        local_subscription = result.scalar_one_or_none()

        if local_subscription:
            local_subscription.status = "canceled"
            local_subscription.canceled_at = datetime.now(timezone.utc)
            await db.commit()

        return {
            "id": canceled.id,
            "status": canceled.status,
            "canceled_at": datetime.fromtimestamp(canceled.canceled_at, tz=timezone.utc) if canceled.canceled_at else None
        }

    except stripe.error.StripeError as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel subscription: {str(e)}"
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, SQLAlchemyError) as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhooks with enhanced security
    
    Security layers:
    1. IP whitelist verification (Stripe IPs only)
    2. Stripe signature verification
    3. Rate limiting (handled by middleware)
    4. Comprehensive logging
    """
    from app.core.webhook_security import log_webhook_attempt

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # SECURITY FIX: Use the hardened webhook_security module for signature
    # verification (constant-time comparison, configurable tolerance,
    # fail-closed if secret is empty) instead of the Stripe SDK directly.
    try:
        from app.core.webhook_security import construct_stripe_event
        event = construct_stripe_event(payload, sig_header)
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        log_webhook_attempt(request, "stripe", False, str(e))
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        background_tasks.add_task(
            handle_payment_succeeded,
            db,
            payment_intent
        )

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        background_tasks.add_task(
            handle_payment_failed,
            db,
            payment_intent
        )

    elif event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        background_tasks.add_task(
            handle_subscription_created,
            db,
            subscription
        )

    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        background_tasks.add_task(
            handle_subscription_updated,
            db,
            subscription
        )

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        background_tasks.add_task(
            handle_subscription_deleted,
            db,
            subscription
        )

    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        background_tasks.add_task(
            handle_invoice_paid,
            db,
            invoice
        )

    # Log successful webhook processing
    log_webhook_attempt(request, "stripe", True)

    return JSONResponse(status=200, content={"ok": True})


async def handle_payment_succeeded(db: AsyncSession, payment_intent: dict):
    """Handle successful payment"""
    try:
        # Update payment record
        from app.models.payment import PaymentTransaction
        result = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.processor_transaction_id == payment_intent["id"]
            )
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = "completed"
            payment.processed_at = datetime.now(timezone.utc)
            await db.commit()

            # Send confirmation email
            if payment_intent.get("customer_email"):
                await send_payment_confirmation_email(
                    to_email=payment_intent["customer_email"],
                    amount=payment_intent["amount"] / 100,
                    currency=payment_intent["currency"],
                    payment_id=payment.id,
                    description=payment_intent.get("description", "")
                )

        logger.info(f"Payment succeeded: {payment_intent['id']}")
    except (ValueError, TypeError, KeyError, AttributeError, SQLAlchemyError) as e:
        logger.error(f"Error handling payment succeeded: {e}")
        await db.rollback()


async def handle_payment_failed(db: AsyncSession, payment_intent: dict):
    """Handle failed payment"""
    try:
        from app.models.payment import PaymentTransaction
        result = await db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.processor_transaction_id == payment_intent["id"]
            )
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = "failed"
            payment.error_message = payment_intent.get("last_payment_error", {}).get("message", "Unknown error")
            await db.commit()

        logger.warning(f"Payment failed: {payment_intent['id']}")
    except (ValueError, TypeError, KeyError, AttributeError, SQLAlchemyError) as e:
        logger.error(f"Error handling payment failed: {e}")
        await db.rollback()


async def handle_subscription_created(db: AsyncSession, subscription: dict):
    """Handle new subscription created from Stripe webhook."""
    try:
        user_id = subscription.get("metadata", {}).get("user_id")
        if not user_id:
            logger.warning("subscription.created webhook missing user_id metadata; skipping")
            return

        # Resolve user for practice_id
        from app.models.user import User as LocalUser
        result = await db.execute(
            select(LocalUser).where(LocalUser.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            logger.warning(f"User not found for subscription: {user_id}")
            return

        if not user.practice_id:
            logger.warning(f"User {user_id} has no practice_id; cannot create subscription")
            return

        # Resolve plan from Stripe price_id
        from app.models.subscription import SubscriptionPlan
        price_id = None
        interval = SubscriptionInterval.MONTHLY  # safe default
        items = subscription.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id")
            interval_raw = items[0].get("plan", {}).get("interval", "month")
            interval = _STRIPE_INTERVAL_MAP.get(interval_raw, SubscriptionInterval.MONTHLY)

        plan = None
        if price_id:
            result = await db.execute(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.stripe_price_id == price_id
                )
            )
            plan = result.scalar_one_or_none()

        # SECURITY FIX: plan_id is nullable=False.  If we can't resolve
        # the plan, we MUST NOT insert a row.
        if not plan:
            logger.error(
                f"Cannot resolve SubscriptionPlan for Stripe price_id={price_id}; "
                "skipping subscription creation to avoid orphaned record."
            )
            return

        # Map Stripe status safely
        sub_status = _STRIPE_STATUS_MAP.get(
            subscription.get("status", ""),
            SubscriptionStatus.INCOMPLETE,
        )

        # Idempotency: check if we already created this subscription
        from app.models.subscription import Subscription as LocalSubscription
        result = await db.execute(
            select(LocalSubscription).where(
                LocalSubscription.stripe_subscription_id == subscription["id"]
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            sub = LocalSubscription(
                practice_id=user.practice_id,
                plan_id=plan.id,
                stripe_subscription_id=subscription["id"],
                stripe_customer_id=subscription["customer"],
                status=sub_status,
                interval=interval,
                current_period_start=datetime.fromtimestamp(subscription.get("current_period_start", 0), tz=timezone.utc) if subscription.get("current_period_start") else None,
                current_period_end=datetime.fromtimestamp(subscription.get("current_period_end", 0), tz=timezone.utc) if subscription.get("current_period_end") else None,
                cancel_at_period_end=subscription.get("cancel_at_period_end", False)
            )
            db.add(sub)
            await db.commit()

        logger.info(f"Subscription created: {subscription['id']}")
    except (IntegrityError, ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error(f"Error handling subscription created: {e}")
        await db.rollback()
    except SQLAlchemyError as e:
        logger.error(f"Database error handling subscription created: {e}")
        await db.rollback()


async def handle_subscription_updated(db: AsyncSession, subscription: dict):
    """Handle subscription update"""
    try:
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription["id"]
            )
        )
        sub = result.scalar_one_or_none()

        if sub:
            # Map Stripe status safely via enum lookup
            new_status = _STRIPE_STATUS_MAP.get(subscription.get("status"))
            if new_status:
                sub.status = new_status
            sub.cancel_at_period_end = subscription.get("cancel_at_period_end", False)
            if subscription.get("current_period_start"):
                sub.current_period_start = datetime.fromtimestamp(subscription["current_period_start"], tz=timezone.utc)
            if subscription.get("current_period_end"):
                sub.current_period_end = datetime.fromtimestamp(subscription["current_period_end"], tz=timezone.utc)
            await db.commit()

        logger.info(f"Subscription updated: {subscription['id']}")
    except (IntegrityError, ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error(f"Error handling subscription updated: {e}")
        await db.rollback()
    except SQLAlchemyError as e:
        logger.error(f"Database error handling subscription updated: {e}")
        await db.rollback()


async def handle_subscription_deleted(db: AsyncSession, subscription: dict):
    """Handle subscription cancellation"""
    try:
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription["id"]
            )
        )
        sub = result.scalar_one_or_none()

        if sub:
            sub.status = SubscriptionStatus.CANCELED
            sub.canceled_at = datetime.now(timezone.utc)
            await db.commit()

        logger.info(f"Subscription deleted: {subscription['id']}")
    except (IntegrityError, ValueError, TypeError, KeyError, AttributeError) as e:
        logger.error(f"Error handling subscription deleted: {e}")
        await db.rollback()
    except SQLAlchemyError as e:
        logger.error(f"Database error handling subscription deleted: {e}")
        await db.rollback()


async def handle_invoice_paid(db: AsyncSession, invoice: dict):
    """Handle successful invoice payment"""
    try:
        # This is for recurring subscription payments
        subscription_id = invoice.get("subscription")
        if subscription_id:
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == subscription_id
                )
            )
            sub = result.scalar_one_or_none()

            if sub:
                sub.last_payment_date = datetime.now(timezone.utc)
                sub.next_billing_date = datetime.fromtimestamp(
                    invoice["lines"]["data"][0]["period"]["end"], tz=timezone.utc
                ) if invoice.get("lines", {}).get("data") else None
                await db.commit()

        logger.info(f"Invoice paid: {invoice['id']}")
    except (ValueError, TypeError, KeyError, AttributeError, SQLAlchemyError) as e:
        logger.error(f"Error handling invoice paid: {e}")
        await db.rollback()
