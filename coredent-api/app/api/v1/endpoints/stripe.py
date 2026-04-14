"""
Stripe Payment Processing Endpoints
Handles payment intents, subscriptions, and webhooks
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import stripe
from datetime import datetime, timedelta
import logging

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.payment import PaymentIntentCreate, PaymentIntentResponse, SubscriptionCreate
from app.core.config import settings
from app.core.email import send_payment_confirmation_email

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    db: Session = Depends(get_db),
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
        db.commit()
        
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
    except Exception as e:
        logger.error(f"Payment intent creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment intent"
        )


@router.post("/create-subscription", response_model=Dict[str, Any])
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
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
    except Exception as e:
        logger.error(f"Subscription creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )


@router.get("/subscription/{subscription_id}")
async def get_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
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
            "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
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
    except Exception as e:
        logger.error(f"Failed to retrieve subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription"
        )


@router.post("/cancel-subscription/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
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
        local_subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if local_subscription:
            local_subscription.status = "canceled"
            local_subscription.canceled_at = datetime.utcnow()
            db.commit()
        
        return {
            "id": canceled.id,
            "status": canceled.status,
            "canceled_at": datetime.fromtimestamp(canceled.canceled_at) if canceled.canceled_at else None
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel subscription: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhooks with enhanced security
    
    Security layers:
    1. IP whitelist verification (Stripe IPs only)
    2. Stripe signature verification
    3. Rate limiting (handled by middleware)
    4. Comprehensive logging
    """
    from app.core.webhook_security import verify_stripe_webhook_security, log_webhook_attempt
    
    # Enhanced security verification
    try:
        await verify_stripe_webhook_security(request)
    except HTTPException as e:
        log_webhook_attempt(request, "stripe", False, str(e.detail))
        raise
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        log_webhook_attempt(request, "stripe", False, "Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        log_webhook_attempt(request, "stripe", False, "Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
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
    
    return JSONResponse(status=200, content={"received": True})


async def handle_payment_succeeded(db: Session, payment_intent: dict):
    """Handle successful payment"""
    try:
        # Update payment record
        from app.models.payment import Payment
        payment = db.query(Payment).filter(
            Payment.transaction_id == payment_intent["id"]
        ).first()
        
        if payment:
            payment.status = "completed"
            payment.paid_at = datetime.utcnow()
            db.commit()
            
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
    except Exception as e:
        logger.error(f"Error handling payment succeeded: {e}")
        db.rollback()


async def handle_payment_failed(db: Session, payment_intent: dict):
    """Handle failed payment"""
    try:
        from app.models.payment import Payment
        payment = db.query(Payment).filter(
            Payment.transaction_id == payment_intent["id"]
        ).first()
        
        if payment:
            payment.status = "failed"
            payment.failure_message = payment_intent.get("last_payment_error", {}).get("message", "Unknown error")
            db.commit()
        
        logger.warning(f"Payment failed: {payment_intent['id']}")
    except Exception as e:
        logger.error(f"Error handling payment failed: {e}")
        db.rollback()


async def handle_subscription_created(db: Session, subscription: dict):
    """Handle new subscription"""
    try:
        user_id = subscription.get("metadata", {}).get("user_id")
        if not user_id:
            return
        
        # Create or update local subscription record
        from app.models.subscription import Subscription as LocalSubscription
        existing = db.query(LocalSubscription).filter(
            LocalSubscription.stripe_subscription_id == subscription["id"]
        ).first()
        
        if not existing:
            sub = LocalSubscription(
                user_id=user_id,
                stripe_subscription_id=subscription["id"],
                stripe_customer_id=subscription["customer"],
                status=subscription["status"],
                current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
                current_period_end=datetime.fromtimestamp(subscription["current_period_end"]),
                cancel_at_period_end=subscription.get("cancel_at_period_end", False)
            )
            db.add(sub)
            db.commit()
        
        logger.info(f"Subscription created: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error handling subscription created: {e}")
        db.rollback()


async def handle_subscription_updated(db: Session, subscription: dict):
    """Handle subscription update"""
    try:
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription["id"]
        ).first()
        
        if sub:
            sub.status = subscription["status"]
            sub.cancel_at_period_end = subscription.get("cancel_at_period_end", False)
            if subscription.get("current_period_start"):
                sub.current_period_start = datetime.fromtimestamp(subscription["current_period_start"])
            if subscription.get("current_period_end"):
                sub.current_period_end = datetime.fromtimestamp(subscription["current_period_end"])
            db.commit()
        
        logger.info(f"Subscription updated: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error handling subscription updated: {e}")
        db.rollback()


async def handle_subscription_deleted(db: Session, subscription: dict):
    """Handle subscription cancellation"""
    try:
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription["id"]
        ).first()
        
        if sub:
            sub.status = "canceled"
            sub.canceled_at = datetime.utcnow()
            db.commit()
        
        logger.info(f"Subscription deleted: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {e}")
        db.rollback()


async def handle_invoice_paid(db: Session, invoice: dict):
    """Handle successful invoice payment"""
    try:
        # This is for recurring subscription payments
        subscription_id = invoice.get("subscription")
        if subscription_id:
            sub = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()
            
            if sub:
                sub.last_payment_date = datetime.utcnow()
                sub.next_billing_date = datetime.fromtimestamp(invoice["lines"]["data"][0]["period"]["end"]) if invoice.get("lines", {}).get("data") else None
                db.commit()
        
        logger.info(f"Invoice paid: {invoice['id']}")
    except Exception as e:
        logger.error(f"Error handling invoice paid: {e}")
        db.rollback()