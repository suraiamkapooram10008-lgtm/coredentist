"""
Payment Endpoints
Stripe integration for processing payments
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Any
from uuid import UUID
import stripe as stripe_lib

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.billing import Invoice, Payment, InvoiceStatus, PaymentStatus
from app.models.patient import Patient
from app.api.deps import get_current_user, verify_csrf
from app.schemas.payment import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentWebhookEvent,
    PaymentMethodAttach,
)

router = APIRouter()

# Initialize Stripe
if settings.STRIPE_API_KEY:
    stripe_lib.api_key = settings.STRIPE_API_KEY


@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: Request,
    payment_data: PaymentIntentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a Stripe PaymentIntent for processing a payment.
    
    Design decisions:
    - Source of truth: Stripe API (creates payment intent)
    - Stored state: Invoice status in database
    - Derived: Payment amount calculated from invoice
    """
    # Verify invoice exists and belongs to practice
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == payment_data.invoice_id,
            Invoice.practice_id == current_user.practice_id,
        )
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice is already paid",
        )
    
    # Verify patient exists
    result = await db.execute(
        select(Patient).where(
            Patient.id == invoice.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    try:
        # Create Stripe PaymentIntent
        payment_amount = payment_data.amount or float(invoice.balance_due)
        
        intent = stripe_lib.PaymentIntent.create(
            amount=int(payment_amount * 100),  # Stripe uses cents
            currency="usd",
            metadata={
                "invoice_id": str(invoice.id),
                "patient_id": str(patient.id),
                "practice_id": str(current_user.practice_id),
            },
            automatic_payment_methods={"enabled": True},
            description=f"Invoice #{invoice.invoice_number}",
        )
        
        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            amount=payment_amount,
            currency="usd",
        )
        
    except stripe_lib.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment error: {str(e)}",
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Handle Stripe webhook events for payment confirmation.
    
    Design decisions:
    - External side effect: Stripe webhook (required useEffect alternative: webhook)
    - Source of truth: Stripe event data
    - Action: Update invoice status based on payment result
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe webhook not configured",
        )
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe_lib.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        )
    except stripe_lib.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )
    
    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        invoice_id = payment_intent.get("metadata", {}).get("invoice_id")
        
        if invoice_id:
            # Update invoice status
            result = await db.execute(
                select(Invoice).where(Invoice.id == UUID(invoice_id))
            )
            invoice = result.scalar_one_or_none()
            
            if invoice:
                invoice.status = InvoiceStatus.PAID
                invoice.balance_due = 0
                
                # Create payment record
                payment = Payment(
                    invoice_id=invoice.id,
                    patient_id=invoice.patient_id,
                    amount=float(payment_intent["amount"] / 100),
                    payment_method="card",
                    transaction_id=payment_intent["id"],
                    status=PaymentStatus.COMPLETED,
                    notes=f"Stripe payment: {payment_intent['id']}",
                )
                db.add(payment)
                await db.commit()
    
    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        invoice_id = payment_intent.get("metadata", {}).get("invoice_id")
        
        if invoice_id:
            # Log failed payment
            result = await db.execute(
                select(Invoice).where(Invoice.id == UUID(invoice_id))
            )
            invoice = result.scalar_one_or_none()
            
            if invoice:
                payment = Payment(
                    invoice_id=invoice.id,
                    patient_id=invoice.patient_id,
                    amount=float(payment_intent["amount"] / 100),
                    payment_method="card",
                    transaction_id=payment_intent["id"],
                    status=PaymentStatus.FAILED,
                    notes=f"Failed: {payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')}",
                )
                db.add(payment)
                await db.commit()
    
    return {"status": "success"}


@router.get("/methods")
async def list_payment_methods(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    List available payment methods for the practice.
    """
    # Return available payment method types
    return {
        "methods": [
            {"type": "card", "enabled": bool(settings.STRIPE_API_KEY)},
            {"type": "bank_transfer", "enabled": False},
        ]
    }


@router.post("/refund")
async def refund_payment(
    request: Request,
    transaction_id: str,
    amount: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Process a refund for a payment.
    """
    # Find the payment
    result = await db.execute(
        select(Payment).where(Payment.transaction_id == transaction_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    # Verify practice ownership
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == payment.invoice_id,
            Invoice.practice_id == current_user.practice_id,
        )
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to refund this payment",
        )
    
    try:
        # Create refund in Stripe
        refund_params = {"payment_intent": transaction_id}
        if amount:
            refund_params["amount"] = int(amount * 100)
        
        refund = stripe_lib.Refund.create(**refund_params)
        
        return {
            "refund_id": refund.id,
            "amount": float(refund.amount / 100),
            "status": refund.status,
        }
        
    except stripe_lib.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund error: {str(e)}",
        )
