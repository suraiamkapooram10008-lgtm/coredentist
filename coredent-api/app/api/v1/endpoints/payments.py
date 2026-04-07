"""
Payment Endpoints
Stripe (US) and Razorpay (India) integration for processing payments
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Any
from uuid import UUID
import stripe as stripe_lib
import razorpay
import hmac
import hashlib

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user, require_role, verify_csrf
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
from app.schemas.payment import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentWebhookEvent,
    PaymentMethodAttach,
    RazorpayOrderCreate,
    RazorpayOrderResponse,
    RazorpayPaymentVerify,
    RazorpayPaymentResponse,
    RazorpayRefundRequest,
    RazorpayRefundResponse,
    RazorpayWebhookEvent,
)
from app.schemas.common import APIResponse

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
        
        # HIPAA: Log payment intent creation
        await log_audit_event(
            db, current_user, "create_payment_intent", "invoice", invoice.id, request,
            {"amount": payment_amount}
        )
        await db.commit()
        
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
    
    return APIResponse(success=True, message="Webhook processed successfully")


@router.get("/methods", response_model=APIResponse)
async def list_payment_methods(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    List available payment methods for the practice.
    """
    methods = [
        {"type": "card", "enabled": bool(settings.STRIPE_API_KEY)},
        {"type": "bank_transfer", "enabled": False},
    ]
    return APIResponse(success=True, data={"methods": methods})


@router.post("/refund")
async def refund_payment(
    request: Request,
    transaction_id: str,
    amount: Optional[float] = None,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
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
        
        # HIPAA: Log refund action
        await log_audit_event(
            db, current_user, "refund_payment", "payment", payment.id, request,
            {"amount": amount or payment.amount, "transaction_id": transaction_id}
        )
        await db.commit()
        
        return APIResponse(
            success=True,
            data={
                "refund_id": refund.id,
                "amount": float(refund.amount / 100),
                "status": refund.status,
            }
        )
        
    except stripe_lib.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund error: {str(e)}",
        )


# ============================================
# Razorpay Endpoints (Indian Market - UPI/Paytm/PhonePe)
# ============================================

# Initialize Razorpay client
razorpay_client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@router.post("/razorpay/create-order", response_model=RazorpayOrderResponse)
async def create_razorpay_order(
    request: Request,
    order_data: RazorpayOrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a Razorpay Order for Indian payments (UPI, Paytm, PhonePe, Cards).
    
    Supports:
    - UPI (Google Pay, PhonePe, Paytm, BHIM)
    - Credit/Debit Cards (Visa, Mastercard, RuPay)
    - Net Banking
    - Wallets (Paytm, Mobikwik, etc.)
    """
    if not razorpay_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay payment gateway not configured",
        )
    
    # Import models here to avoid circular imports
    from app.models.billing import Invoice, InvoiceStatus
    from app.models.patient import Patient
    
    # Verify invoice exists
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == order_data.invoice_id,
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
    
    # Calculate amount in paise (smallest currency unit)
    amount = order_data.amount or float(invoice.balance_due)
    amount_paise = int(amount * 100)  # Convert INR to paise
    
    try:
        # Create Razorpay order
        order = razorpay_client.order.create({
            "amount": amount_paise,
            "currency": order_data.currency,
            "receipt": order_data.receipt or f"invoice_{invoice.id}",
            "payment_capture": 1,  # Auto-capture
            "notes": {
                "invoice_id": str(invoice.id),
                "patient_id": str(invoice.patient_id),
                "practice_id": str(current_user.practice_id),
            },
        })
        
        # HIPAA: Log order creation
        await log_audit_event(
            db, current_user, "create_razorpay_order", "invoice", invoice.id, request,
            {"amount": amount, "currency": order_data.currency}
        )
        await db.commit()
        
        return RazorpayOrderResponse(
            order_id=order["id"],
            amount=order["amount"],
            currency=order["currency"],
            receipt=order["receipt"],
            key_id=settings.RAZORPAY_KEY_ID,
            status=order["status"],
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Razorpay order creation error: {str(e)}",
        )


@router.post("/razorpay/verify-payment", response_model=RazorpayPaymentResponse)
async def verify_razorpay_payment(
    request: Request,
    verify_data: RazorpayPaymentVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Verify a Razorpay payment signature and update invoice status.
    """
    if not razorpay_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay payment gateway not configured",
        )
    
    # Import models
    from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus
    from app.models.patient import Patient
    
    try:
        # Verify payment signature
        params = f"{verify_data.razorpay_order_id}|{verify_data.razorpay_payment_id}"
        expected_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            params.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        if expected_signature != verify_data.razorpay_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment signature",
            )
        
        # Fetch payment details from Razorpay
        payment = razorpay_client.payment.fetch(verify_data.razorpay_payment_id)
        
        # Update invoice status
        result = await db.execute(
            select(Invoice).where(Invoice.id == verify_data.invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if invoice:
            invoice.status = InvoiceStatus.PAID
            invoice.balance_due = 0
            
            # Create payment record
            payment_record = Payment(
                invoice_id=invoice.id,
                patient_id=invoice.patient_id,
                amount=float(payment["amount"] / 100),  # Convert paise to INR
                payment_method=payment.get("method", "upi"),
                transaction_id=verify_data.razorpay_payment_id,
                status=PaymentStatus.COMPLETED,
                notes=f"Razorpay payment: {verify_data.razorpay_payment_id}",
            )
            db.add(payment_record)
            await db.commit()
        
        # HIPAA: Log payment verification
        await log_audit_event(
            db, current_user, "verify_razorpay_payment", "invoice", verify_data.invoice_id, request,
            {"payment_id": verify_data.razorpay_payment_id}
        )
        await db.commit()
        
        return RazorpayPaymentResponse(
            payment_id=verify_data.razorpay_payment_id,
            order_id=verify_data.razorpay_order_id,
            amount=float(payment["amount"] / 100),
            currency=payment.get("currency", "INR"),
            status="captured",
            method=payment.get("method", "upi"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment verification error: {str(e)}",
        )


@router.post("/razorpay/refund", response_model=RazorpayRefundResponse)
async def refund_razorpay_payment(
    request: Request,
    refund_data: RazorpayRefundRequest,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Process a refund for a Razorpay payment.
    """
    if not razorpay_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Razorpay payment gateway not configured",
        )
    
    # Import models
    from app.models.billing import Payment, PaymentStatus
    
    try:
        # Find the payment
        result = await db.execute(
            select(Payment).where(Payment.transaction_id == refund_data.payment_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )
        
        # Process refund
        refund_params = {"payment_id": refund_data.payment_id}
        if refund_data.amount:
            refund_params["amount"] = int(refund_data.amount * 100)  # Convert to paise
        
        refund = razorpay_client.refund.create(refund_params)
        
        # Update payment status
        payment.status = PaymentStatus.REFUNDED
        await db.commit()
        
        # HIPAA: Log refund
        await log_audit_event(
            db, current_user, "refund_razorpay_payment", "payment", payment.id, request,
            {"refund_id": refund["id"], "amount": refund_data.amount or payment.amount}
        )
        await db.commit()
        
        return RazorpayRefundResponse(
            refund_id=refund["id"],
            amount=float(refund["amount"] / 100),
            status=refund["status"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund error: {str(e)}",
        )


@router.post("/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Handle Razorpay webhook events for payment confirmation.
    """
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Razorpay webhook not configured",
        )
    
    # Import models
    from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus
    
    # Verify webhook signature
    signature = request.headers.get("X-Razorpay-Signature")
    body = await request.body()
    
    expected_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    
    if signature != expected_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )
    
    # Parse webhook payload
    import json
    payload = json.loads(body)
    event = payload.get("event", "")
    
    if event == "payment.captured":
        payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        invoice_id = payment_data.get("notes", {}).get("invoice_id")
        
        if invoice_id:
            result = await db.execute(
                select(Invoice).where(Invoice.id == UUID(invoice_id))
            )
            invoice = result.scalar_one_or_none()
            
            if invoice:
                invoice.status = InvoiceStatus.PAID
                invoice.balance_due = 0
                
                payment_record = Payment(
                    invoice_id=invoice.id,
                    patient_id=invoice.patient_id,
                    amount=float(payment_data["amount"] / 100),
                    payment_method=payment_data.get("method", "upi"),
                    transaction_id=payment_data["id"],
                    status=PaymentStatus.COMPLETED,
                    notes=f"Razorpay webhook: {payment_data['id']}",
                )
                db.add(payment_record)
                await db.commit()
    
    elif event == "payment.failed":
        payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        invoice_id = payment_data.get("notes", {}).get("invoice_id")
        
        if invoice_id:
            result = await db.execute(
                select(Invoice).where(Invoice.id == UUID(invoice_id))
            )
            invoice = result.scalar_one_or_none()
            
            if invoice:
                payment_record = Payment(
                    invoice_id=invoice.id,
                    patient_id=invoice.patient_id,
                    amount=float(payment_data["amount"] / 100),
                    payment_method=payment_data.get("method", "upi"),
                    transaction_id=payment_data["id"],
                    status=PaymentStatus.FAILED,
                    notes=f"Razorpay payment failed: {payment_data.get('error_description', 'Unknown')}",
                )
                db.add(payment_record)
                await db.commit()
    
    return APIResponse(success=True, message="Razorpay webhook processed successfully")
