"""
Payment Endpoints
Stripe (US) and Razorpay (India) integration for processing payments
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
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
from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus
from app.models.patient import Patient

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
        # Note: log_audit_event commits internally, no need for double commit
        
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


@router.post("/webhooks/stripe")  # Separate route prefix for webhooks
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Handle Stripe webhook events for payment confirmation.
    
    SECURITY: Webhook endpoint with signature verification.
    No CSRF required as Stripe signs requests.
    
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
        # Note: log_audit_event commits internally
        
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
        # Note: log_audit_event commits internally
        
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
            
            # HIPAA: Log payment verification
            await log_audit_event(
                db, current_user, "verify_razorpay_payment", "invoice", verify_data.invoice_id, request,
                {"payment_id": verify_data.razorpay_payment_id}
            )
            # Note: log_audit_event commits internally, includes payment_record
        
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
        
        # HIPAA: Log refund
        await log_audit_event(
            db, current_user, "refund_razorpay_payment", "payment", payment.id, request,
            {"refund_id": refund["id"], "amount": refund_data.amount or payment.amount}
        )
        # Note: log_audit_event commits internally, includes payment status update
        
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


# ============================================
# Payment Dashboard Endpoints
# ============================================

@router.get("/stats", response_model=dict)
async def get_payment_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get payment statistics for the practice dashboard
    """
    from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus
    from datetime import datetime, timedelta
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    
    # Today's revenue (paid invoices today)
    today_result = await db.execute(
        select(Invoice).where(
            Invoice.practice_id == current_user.practice_id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.updated_at >= today_start,
        )
    )
    today_invoices = today_result.scalars().all()
    today_revenue = sum(float(inv.total_amount) for inv in today_invoices)
    today_transactions = len(today_invoices)
    
    # This month's revenue
    month_result = await db.execute(
        select(Invoice).where(
            Invoice.practice_id == current_user.practice_id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.updated_at >= month_start,
        )
    )
    month_invoices = month_result.scalars().all()
    month_revenue = sum(float(inv.total_amount) for inv in month_invoices)
    
    # Last month's revenue for growth calculation
    last_month_result = await db.execute(
        select(Invoice).where(
            Invoice.practice_id == current_user.practice_id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.updated_at >= last_month_start,
            Invoice.updated_at < month_start,
        )
    )
    last_month_invoices = last_month_result.scalars().all()
    last_month_revenue = sum(float(inv.total_amount) for inv in last_month_invoices)
    
    # Calculate growth percentage
    if last_month_revenue > 0:
        month_growth = round(((month_revenue - last_month_revenue) / last_month_revenue) * 100, 1)
    else:
        month_growth = 0 if month_revenue == 0 else 100
    
    # Pending payments
    pending_result = await db.execute(
        select(Invoice).where(
            Invoice.practice_id == current_user.practice_id,
            Invoice.status == InvoiceStatus.PENDING,
        )
    )
    pending_invoices = pending_result.scalars().all()
    pending_amount = sum(float(inv.balance_due) for inv in pending_invoices)
    pending_count = len(pending_invoices)
    
    # Recurring revenue - Calculate from recurring billing records
    # Query active recurring billing plans
    from app.models.payment import RecurringBilling, RecurringStatus
    
    recurring_result = await db.execute(
        select(RecurringBilling).where(
            RecurringBilling.practice_id == current_user.practice_id,
            RecurringBilling.status == RecurringStatus.ACTIVE,
        )
    )
    recurring_plans = recurring_result.scalars().all()
    
    # Calculate monthly recurring revenue (MRR)
    recurring_revenue = 0.0
    for plan in recurring_plans:
        # Convert all intervals to monthly equivalent
        amount = float(plan.amount)
        if plan.interval == "monthly":
            recurring_revenue += amount
        elif plan.interval == "quarterly":
            recurring_revenue += amount / 3  # Quarterly to monthly
        elif plan.interval == "yearly":
            recurring_revenue += amount / 12  # Yearly to monthly
        elif plan.interval == "weekly":
            recurring_revenue += amount * 4.33  # Weekly to monthly (avg 4.33 weeks/month)
    
    return {
        "todayRevenue": today_revenue,
        "todayTransactions": today_transactions,
        "monthRevenue": month_revenue,
        "monthGrowth": month_growth,
        "pendingPayments": pending_amount,
        "pendingCount": pending_count,
        "recurringRevenue": round(recurring_revenue, 2),  # Monthly Recurring Revenue (MRR)
    }


@router.get("/transactions", response_model=dict)
async def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),  # Add CSRF protection
) -> Any:
    """
    List payment transactions (CSRF protected)
    """
    from app.models.billing import Invoice, Payment, PaymentStatus
    
    query = (
        select(Payment)
        .join(Invoice)
        .where(Invoice.practice_id == current_user.practice_id)
        .order_by(Payment.created_at.desc())
    )
    
    if status:
        status_enum = PaymentStatus(status)
        query = query.where(Payment.status == status_enum)
    
    # Get total count
    count_query = select(Payment).join(Invoice).where(
        Invoice.practice_id == current_user.practice_id
    )
    if status:
        count_query = count_query.where(Payment.status == PaymentStatus(status))
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    transactions = []
    for payment in payments:
        transactions.append({
            "id": str(payment.id),
            "amount": float(payment.amount),
            "status": payment.status.value if payment.status else "unknown",
            "method": payment.payment_method,
            "transactionId": payment.transaction_id,
            "createdAt": payment.created_at.isoformat() if payment.created_at else None,
        })
    
    return {
        "transactions": transactions,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/recurring-plans", response_model=dict)
async def list_recurring_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List recurring payment plans (subscription plans for patients)
    """
    # Return sample recurring plans - in production these would be stored in database
    plans = [
        {
            "id": "plan_basic_cleaning",
            "name": "Basic Cleaning Plan",
            "description": "Bi-annual professional cleaning",
            "amount": 199.99,
            "currency": "USD",
            "interval": "6_months",
            "features": ["2 cleanings per year", "10% discount on other services"],
        },
        {
            "id": "plan_premium_care",
            "name": "Premium Care Plan",
            "description": "Quarterly cleaning + comprehensive care",
            "amount": 499.99,
            "currency": "USD",
            "interval": "quarterly",
            "features": ["4 cleanings per year", "15% discount on all services", "Priority scheduling"],
        },
        {
            "id": "plan_family_care",
            "name": "Family Care Plan",
            "description": "Coverage for up to 4 family members",
            "amount": 899.99,
            "currency": "USD",
            "interval": "yearly",
            "features": ["Coverage for 4 members", "Unlimited cleanings", "20% discount on all services"],
        },
    ]
    return {"plans": plans}


@router.get("/terminals", response_model=dict)
async def list_terminals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List payment terminals configured for the practice
    """
    terminals = []
    
    # Add Stripe terminal if configured
    if settings.STRIPE_API_KEY:
        terminals.append({
            "id": "stripe_terminal",
            "name": "Stripe Terminal",
            "type": "stripe",
            "status": "active",
            "location": "Cloud",
        })
    
    # Add Razorpay terminal if configured
    if settings.RAZORPAY_KEY_ID:
        terminals.append({
            "id": "razorpay_terminal",
            "name": "Razorpay Terminal",
            "type": "razorpay",
            "status": "active",
            "location": "Cloud",
        })
    
    return {"terminals": terminals}


@router.post("/webhooks/razorpay")  # Separate route prefix for webhooks
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Handle Razorpay webhook events for payment confirmation.
    
    SECURITY: Webhook endpoint with signature verification.
    No CSRF required as Razorpay signs requests.
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
