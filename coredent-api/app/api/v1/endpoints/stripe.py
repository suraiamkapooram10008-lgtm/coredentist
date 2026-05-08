"""
Stripe Payment Processing Endpoints
Handles payment intents, subscriptions, and webhooks
"""

from typing import Any, Dict, List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import stripe as stripe_lib
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.config_simple import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.payment import PaymentIntentCreate, PaymentIntentResponse
from app.schemas.subscription import SubscriptionCreate
from app.core.email import email_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Stripe globally
if settings.STRIPE_API_KEY:
    stripe_lib.api_key = settings.STRIPE_API_KEY

# Idempotency store for Stripe webhooks — prevents duplicate event processing (e.g., double charges)
_processed_webhooks: set[str] = set()
_MAX_WEBHOOK_CACHE = 1000


@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe payment intent for one-time payments
    """
    if not settings.STRIPE_API_KEY:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stripe not configured")

    try:
        intent = stripe_lib.PaymentIntent.create(
            amount=int(payment_data.amount * 100),
            currency=payment_data.currency.lower(),
            customer_email=current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "practice_id": str(current_user.practice_id) if current_user.practice_id else "",
                "payment_type": payment_data.payment_type,
                "description": payment_data.description
            },
            automatic_payment_methods={"enabled": True},
        )
        
        # Log payment intent
        from app.models.payment import Payment
        payment = Payment(
            patient_id=payment_data.patient_id if hasattr(payment_data, 'patient_id') else None,
            amount=payment_data.amount,
            currency=payment_data.currency,
            status="pending",
            payment_method="stripe",
            transaction_id=intent.id,
            description=payment_data.description,
        )
        db.add(payment)
        await db.commit()
        
        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            amount=payment_data.amount,
            currency=payment_data.currency
        )
        
    except stripe_lib.error.StripeError as e:
        logger.error(f"Stripe error creating payment intent: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment processing failed. Please try again or contact support.")


@router.post("/create-subscription")
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new Stripe subscription"""
    if not settings.STRIPE_API_KEY:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stripe not configured")

    try:
        customer = stripe_lib.Customer.create(
            email=current_user.email,
            name=f"{current_user.first_name} {current_user.last_name}",
            metadata={"user_id": str(current_user.id), "practice_id": str(current_user.practice_id) if current_user.practice_id else ""}
        )
        
        subscription = stripe_lib.Subscription.create(
            customer=customer.id,
            items=[{"price": subscription_data.price_id, "quantity": subscription_data.quantity or 1}],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
            metadata={"user_id": str(current_user.id), "subscription_type": subscription_data.subscription_type}
        )
        
        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice.payment_intent else None,
            "customer_id": customer.id,
            "status": subscription.status
        }
        
    except stripe_lib.error.StripeError as e:
        logger.error(f"Stripe error creating subscription: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription setup failed. Please try again or contact support.")


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhooks with idempotency and security
    Includes IP whitelist verification for production security
    """
    from app.core.webhook_security import verify_stripe_webhook_security, log_webhook_attempt
    import ipaddress
    
    # REC-12: Stripe webhook IP whitelist verification
    if settings.STRIPE_WEBHOOK_IP_WHITELIST_ENABLED and settings.ENVIRONMENT == "production":
        client_ip = request.client.host if request.client else None
        if not client_ip:
            logger.warning("Stripe webhook: No client IP found")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        # Check if client IP is in whitelist (supports both single IPs and CIDR)
        ip_allowed = False
        try:
            client_addr = ipaddress.ip_address(client_ip)
            for allowed_net in settings.STRIPE_WEBHOOK_IP_WHITELIST:
                if client_addr in ipaddress.ip_network(allowed_net, strict=False):
                    ip_allowed = True
                    break
        except ValueError:
            # If IP parsing fails, check as string (for IPv6 or unusual formats)
            ip_allowed = client_ip in settings.STRIPE_WEBHOOK_IP_WHITELIST
        
        if not ip_allowed:
            logger.warning(f"Stripe webhook: IP {client_ip} not in whitelist")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: IP not authorized")
    
    payload = await request.body()
    if len(payload) > 2 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Payload too large")
    
    sig_header = request.headers.get("stripe-signature")
    if not sig_header or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature or webhook secret")

    try:
        event = stripe_lib.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe_lib.error.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    event_id = event["id"]
    event_type = event["type"]
    
    # IDEMPOTENCY: Prevent duplicate processing (double charges, duplicate subscriptions)
    if event_id in _processed_webhooks:
        logger.info(f"Skipping duplicate webhook: {event_type} ({event_id})")
        return JSONResponse(status_code=200, content={"received": True, "duplicate": True})
    
    _processed_webhooks.add(event_id)
    if len(_processed_webhooks) > _MAX_WEBHOOK_CACHE:
        _processed_webhooks.clear()
    
    logger.info(f"Processing webhook: {event_type} ({event_id})")
    
    event_data = event["data"]["object"]
    
    try:
        if event_type == "payment_intent.succeeded":
            await _handle_payment_succeeded(db, event_data)
        elif event_type == "payment_intent.payment_failed":
            await _handle_payment_failed(db, event_data)
        elif event_type == "customer.subscription.created":
            await _handle_subscription_created(db, event_data)
        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(db, event_data)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(db, event_data)
        elif event_type == "invoice.payment_succeeded":
            await _handle_invoice_paid(db, event_data)
        else:
            logger.debug(f"Unhandled webhook event type: {event_type}")
    except Exception as e:
        logger.error(f"Error processing webhook {event_id}: {e}")
        # Return 200 to prevent Stripe retries for non-critical errors

    return JSONResponse(status_code=200, content={"received": True})


async def _handle_payment_succeeded(db: AsyncSession, payment_intent: dict):
    """Handle successful payment"""
    try:
        from app.models.payment import Payment
        result = await db.execute(select(Payment).where(Payment.transaction_id == payment_intent["id"]))
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = "completed"
            payment.paid_at = datetime.now(timezone.utc)
            await db.commit()
        logger.info(f"Payment succeeded: {payment_intent['id']}")
    except Exception as e:
        logger.error(f"Error handling payment succeeded: {e}")
        await db.rollback()


async def _handle_payment_failed(db: AsyncSession, payment_intent: dict):
    """Handle failed payment"""
    try:
        from app.models.payment import Payment
        result = await db.execute(select(Payment).where(Payment.transaction_id == payment_intent["id"]))
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = "failed"
            payment.failure_message = payment_intent.get("last_payment_error", {}).get("message", "Unknown error")
            await db.commit()
        logger.warning(f"Payment failed: {payment_intent['id']}")
    except Exception as e:
        logger.error(f"Error handling payment failed: {e}")
        await db.rollback()


async def _handle_subscription_created(db: AsyncSession, subscription: dict):
    """Handle new subscription"""
    try:
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == subscription["id"])
        )
        existing = result.scalar_one_or_none()
        if not existing:
            sub = Subscription(
                practice_id=subscription.get("metadata", {}).get("practice_id"),
                stripe_subscription_id=subscription["id"],
                stripe_customer_id=subscription["customer"],
                status=subscription["status"],
                current_period_start=datetime.fromtimestamp(subscription["current_period_start"], tz=timezone.utc),
                current_period_end=datetime.fromtimestamp(subscription["current_period_end"], tz=timezone.utc),
                cancel_at_period_end=subscription.get("cancel_at_period_end", False)
            )
            db.add(sub)
            await db.commit()
        logger.info(f"Subscription created: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error handling subscription created: {e}")
        await db.rollback()


async def _handle_subscription_updated(db: AsyncSession, subscription: dict):
    """Handle subscription update"""
    try:
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == subscription["id"])
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = subscription["status"]
            sub.cancel_at_period_end = subscription.get("cancel_at_period_end", False)
            if subscription.get("current_period_start"):
                sub.current_period_start = datetime.fromtimestamp(subscription["current_period_start"], tz=timezone.utc)
            if subscription.get("current_period_end"):
                sub.current_period_end = datetime.fromtimestamp(subscription["current_period_end"], tz=timezone.utc)
            await db.commit()
        logger.info(f"Subscription updated: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error handling subscription updated: {e}")
        await db.rollback()


async def _handle_subscription_deleted(db: AsyncSession, subscription: dict):
    """Handle subscription cancellation"""
    try:
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == subscription["id"])
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = "canceled"
            sub.canceled_at = datetime.now(timezone.utc)
            await db.commit()
        logger.info(f"Subscription deleted: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {e}")
        await db.rollback()


async def _handle_invoice_paid(db: AsyncSession, invoice: dict):
    """Handle successful invoice payment"""
    try:
        subscription_id = invoice.get("subscription")
        if subscription_id:
            result = await db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.last_payment_date = datetime.now(timezone.utc)
                period_end = invoice.get("lines", {}).get("data", [{}])[0].get("period", {}).get("end")
                if period_end:
                    sub.next_billing_date = datetime.fromtimestamp(period_end, tz=timezone.utc)
                await db.commit()
        logger.info(f"Invoice paid: {invoice['id']}")
    except Exception as e:
        logger.error(f"Error handling invoice paid: {e}")
        await db.rollback()