"""
Payment Endpoints (Refactored)
Stripe (US) and Razorpay (India) integration for processing payments
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Any
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.config_simple import settings
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
from app.services.payment_service import PaymentService
from app.services.payment_processing import (
    StripePaymentProcessor,
    RazorpayPaymentProcessor,
    WebhookProcessor,
)
from app.services.payment_reconciliation import PaymentReconciliationService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Stripe Endpoints (US Market)
# ============================================

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
    try:
        # Create payment intent using service
        intent_data = await StripePaymentProcessor.create_payment_intent(
            db, current_user, payment_data.invoice_id, payment_data.amount
        )
        
        # HIPAA: Log payment intent creation
        await log_audit_event(
            db, current_user, "create_payment_intent", "invoice", payment_data.invoice_id, request,
            {"amount": intent_data["amount"]}
        )
        
        return PaymentIntentResponse(**intent_data)
        
    except ValueError as e:
        logger.warning(f"Invalid payment intent request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Payment intent creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment error: {str(e)}",
        )


@router.post("/webhooks/stripe")
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
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        # Verify and parse webhook
        event = WebhookProcessor.verify_stripe_signature(payload, sig_header)
        
        # Handle the event
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            await StripePaymentProcessor.handle_payment_succeeded(db, payment_intent)
        
        elif event["type"] == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            await StripePaymentProcessor.handle_payment_failed(db, payment_intent)
        
        logger.info(f"Processed Stripe webhook: {event['type']}")
        return APIResponse(success=True, message="Webhook processed successfully")
        
    except ValueError as e:
        logger.warning(f"Invalid Stripe webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing error",
        )


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
    try:
        # Find the payment
        payment = await PaymentService.get_payment(db, transaction_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )
        
        # Verify practice ownership
        invoice = await PaymentService.get_invoice(db, payment.invoice_id, current_user.practice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to refund this payment",
            )
        
        # Process refund
        refund_data = await StripePaymentProcessor.process_refund(
            db, transaction_id, amount
        )
        
        # HIPAA: Log refund action
        await log_audit_event(
            db, current_user, "refund_payment", "payment", payment.id, request,
            {"amount": amount or payment.amount, "transaction_id": transaction_id}
        )
        
        return APIResponse(success=True, data=refund_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refund error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund error: {str(e)}",
        )


@router.get("/methods", response_model=APIResponse)
async def list_payment_methods(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List available payment methods for the practice.
    """
    methods = await PaymentReconciliationService.get_payment_methods_status(
        db, current_user.practice_id
    )
    return APIResponse(success=True, data={"methods": methods})


# ============================================
# Razorpay Endpoints (Indian Market - UPI/Paytm/PhonePe)
# ============================================

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
    try:
        # Create order using service
        order_data_response = await RazorpayPaymentProcessor.create_order(
            db, current_user, order_data.invoice_id, order_data.amount,
            order_data.currency, order_data.receipt
        )
        
        # HIPAA: Log order creation
        await log_audit_event(
            db, current_user, "create_razorpay_order", "invoice", order_data.invoice_id, request,
            {"amount": order_data.amount, "currency": order_data.currency}
        )
        
        return RazorpayOrderResponse(**order_data_response)
        
    except ValueError as e:
        logger.warning(f"Invalid Razorpay order request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "not found" not in str(e).lower() else status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Razorpay order creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE if "not configured" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(e),
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
    try:
        # Verify payment using service
        payment_data = await RazorpayPaymentProcessor.verify_payment(
            db,
            verify_data.invoice_id,
            verify_data.razorpay_order_id,
            verify_data.razorpay_payment_id,
            verify_data.razorpay_signature,
        )
        
        # HIPAA: Log payment verification
        await log_audit_event(
            db, current_user, "verify_razorpay_payment", "invoice", verify_data.invoice_id, request,
            {"payment_id": verify_data.razorpay_payment_id}
        )
        
        return RazorpayPaymentResponse(**payment_data)
        
    except ValueError as e:
        logger.warning(f"Invalid Razorpay payment verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
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
    try:
        # Process refund using service
        refund_response = await RazorpayPaymentProcessor.process_refund(
            db, refund_data.payment_id, refund_data.amount
        )
        
        # HIPAA: Log refund
        payment = await PaymentService.get_payment(db, refund_data.payment_id)
        if payment:
            await log_audit_event(
                db, current_user, "refund_razorpay_payment", "payment", payment.id, request,
                {"refund_id": refund_response["refund_id"], "amount": refund_data.amount or payment.amount}
            )
        
        return RazorpayRefundResponse(**refund_response)
        
    except ValueError as e:
        logger.warning(f"Invalid Razorpay refund request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "not found" not in str(e).lower() else status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Razorpay refund error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE if "not configured" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
            detail=f"Refund error: {str(e)}",
        )


@router.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Handle Razorpay webhook events for payment confirmation.
    
    SECURITY: Webhook endpoint with signature verification.
    No CSRF required as Razorpay signs requests.
    """
    try:
        signature = request.headers.get("X-Razorpay-Signature")
        body = await request.body()
        
        # Verify and parse webhook
        payload = WebhookProcessor.verify_razorpay_signature(body, signature)
        
        event = payload.get("event", "")
        
        if event == "payment.captured":
            payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
            invoice_id = payment_data.get("notes", {}).get("invoice_id")
            
            if invoice_id:
                # Create payment record
                invoice = await PaymentService.get_invoice(db, UUID(invoice_id))
                if invoice:
                    await PaymentService.create_payment_record(
                        db=db,
                        invoice_id=invoice.id,
                        patient_id=invoice.patient_id,
                        amount=float(payment_data["amount"] / 100),
                        payment_method=payment_data.get("method", "upi"),
                        transaction_id=payment_data["id"],
                        status="completed",
                        notes=f"Razorpay webhook: {payment_data['id']}",
                    )
        
        elif event == "payment.failed":
            payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
            invoice_id = payment_data.get("notes", {}).get("invoice_id")
            
            if invoice_id:
                invoice = await PaymentService.get_invoice(db, UUID(invoice_id))
                if invoice:
                    await PaymentService.create_payment_record(
                        db=db,
                        invoice_id=invoice.id,
                        patient_id=invoice.patient_id,
                        amount=float(payment_data["amount"] / 100),
                        payment_method=payment_data.get("method", "upi"),
                        transaction_id=payment_data["id"],
                        status="failed",
                        notes=f"Razorpay payment failed: {payment_data.get('error_description', 'Unknown')}",
                    )
        
        logger.info(f"Processed Razorpay webhook: {event}")
        return APIResponse(success=True, message="Razorpay webhook processed successfully")
        
    except ValueError as e:
        logger.warning(f"Invalid Razorpay webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Razorpay webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing error",
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
    try:
        # Get payment stats using service
        stats = await PaymentService.get_payment_stats(db, current_user.practice_id)
        
        # Get recurring revenue
        recurring_revenue = await PaymentReconciliationService.get_recurring_revenue(
            db, current_user.practice_id
        )
        
        return {
            "todayRevenue": stats["today_revenue"],
            "todayTransactions": stats["today_transactions"],
            "monthRevenue": stats["month_revenue"],
            "monthGrowth": stats["month_growth"],
            "pendingPayments": stats["pending_amount"],
            "pendingCount": stats["pending_count"],
            "recurringRevenue": recurring_revenue,
        }
        
    except Exception as e:
        logger.error(f"Error getting payment stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving payment statistics",
        )


@router.get("/transactions", response_model=dict)
async def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    List payment transactions (CSRF protected)
    """
    try:
        # Get transactions using service
        offset = (page - 1) * limit
        payments, total = await PaymentService.list_payments(
            db, current_user.practice_id, status=status, limit=limit, offset=offset
        )
        
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
        
    except Exception as e:
        logger.error(f"Error listing transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving transactions",
        )


@router.get("/recurring-plans", response_model=dict)
async def list_recurring_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List recurring payment plans (subscription plans for patients)
    """
    try:
        plans = await PaymentReconciliationService.get_recurring_plans(
            db, current_user.practice_id
        )
        return {"plans": plans}
    except Exception as e:
        logger.error(f"Error listing recurring plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving recurring plans",
        )


@router.get("/terminals", response_model=dict)
async def list_terminals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List payment terminals configured for the practice
    """
    try:
        terminals = await PaymentReconciliationService.get_payment_terminals(
            db, current_user.practice_id
        )
        return {"terminals": terminals}
    except Exception as e:
        logger.error(f"Error listing terminals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving terminals",
        )
