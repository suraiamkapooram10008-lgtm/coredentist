"""
Payment Processing Service
Handles Stripe and Razorpay payment processing
"""

from typing import Optional, Dict, Any
from uuid import UUID
import logging
import hmac
import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession
import stripe as stripe_lib
import razorpay

from app.core.config_simple import settings
from app.models.billing import InvoiceStatus, Payment, PaymentStatus
from app.models.user import User
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


class StripePaymentProcessor:
    """Handles Stripe payment processing"""

    @staticmethod
    async def create_payment_intent(
        db: AsyncSession,
        current_user: User,
        invoice_id: UUID,
        amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Create a Stripe PaymentIntent"""
        if not settings.STRIPE_API_KEY:
            raise ValueError("Stripe API key not configured")

        stripe_lib.api_key = settings.STRIPE_API_KEY

        # Get invoice
        invoice = await PaymentService.get_invoice(db, invoice_id, current_user.practice_id)
        if not invoice:
            raise ValueError("Invoice not found")

        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Invoice is already paid")

        try:
            # Create Stripe PaymentIntent
            payment_amount = amount or float(invoice.balance_due)

            intent = stripe_lib.PaymentIntent.create(
                amount=int(payment_amount * 100),  # Stripe uses cents
                currency="usd",
                metadata={
                    "invoice_id": str(invoice.id),
                    "patient_id": str(invoice.patient_id),
                    "practice_id": str(current_user.practice_id),
                },
                automatic_payment_methods={"enabled": True},
                description=f"Invoice #{invoice.invoice_number}",
            )

            logger.info(f"Created Stripe PaymentIntent: {intent.id}")

            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": payment_amount,
                "currency": "usd",
            }

        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise

    @staticmethod
    async def handle_payment_succeeded(
        db: AsyncSession,
        payment_intent: Dict[str, Any],
    ) -> Optional[Payment]:
        """Handle successful Stripe payment"""
        invoice_id = payment_intent.get("metadata", {}).get("invoice_id")

        if not invoice_id:
            logger.warning("No invoice_id in payment intent metadata")
            return None

        try:
            invoice_uuid = UUID(invoice_id)

            # Mark invoice as paid
            invoice = await PaymentService.mark_invoice_paid(db, invoice_uuid)
            if not invoice:
                logger.warning(f"Invoice not found: {invoice_id}")
                return None

            # Create payment record
            payment = await PaymentService.create_payment_record(
                db=db,
                invoice_id=invoice.id,
                patient_id=invoice.patient_id,
                amount=float(payment_intent["amount"] / 100),
                payment_method="card",
                transaction_id=payment_intent["id"],
                status=PaymentStatus.COMPLETED,
                notes=f"Stripe payment: {payment_intent['id']}",
            )

            logger.info(f"Processed successful Stripe payment: {payment_intent['id']}")
            return payment

        except Exception as e:
            logger.error(f"Error handling payment succeeded: {str(e)}")
            raise

    @staticmethod
    async def handle_payment_failed(
        db: AsyncSession,
        payment_intent: Dict[str, Any],
    ) -> Optional[Payment]:
        """Handle failed Stripe payment"""
        invoice_id = payment_intent.get("metadata", {}).get("invoice_id")

        if not invoice_id:
            logger.warning("No invoice_id in payment intent metadata")
            return None

        try:
            invoice_uuid = UUID(invoice_id)
            invoice = await PaymentService.get_invoice(db, invoice_uuid)

            if not invoice:
                logger.warning(f"Invoice not found: {invoice_id}")
                return None

            # Create failed payment record
            payment = await PaymentService.create_payment_record(
                db=db,
                invoice_id=invoice.id,
                patient_id=invoice.patient_id,
                amount=float(payment_intent["amount"] / 100),
                payment_method="card",
                transaction_id=payment_intent["id"],
                status=PaymentStatus.FAILED,
                notes=f"Failed: {payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')}",
            )

            logger.info(f"Recorded failed Stripe payment: {payment_intent['id']}")
            return payment

        except Exception as e:
            logger.error(f"Error handling payment failed: {str(e)}")
            raise

    @staticmethod
    async def process_refund(
        db: AsyncSession,
        transaction_id: str,
        amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Process a Stripe refund"""
        if not settings.STRIPE_API_KEY:
            raise ValueError("Stripe API key not configured")

        stripe_lib.api_key = settings.STRIPE_API_KEY

        try:
            refund_params = {"payment_intent": transaction_id}
            if amount:
                refund_params["amount"] = int(amount * 100)

            refund = stripe_lib.Refund.create(**refund_params)

            logger.info(f"Processed Stripe refund: {refund.id}")

            return {
                "refund_id": refund.id,
                "amount": float(refund.amount / 100),
                "status": refund.status,
            }

        except stripe_lib.error.StripeError as e:
            logger.error(f"Stripe refund error: {str(e)}")
            raise


class RazorpayPaymentProcessor:
    """Handles Razorpay payment processing"""

    @staticmethod
    def _get_client() -> razorpay.Client:
        """Get Razorpay client"""
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise ValueError("Razorpay credentials not configured")

        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    @staticmethod
    async def create_order(
        db: AsyncSession,
        current_user: User,
        invoice_id: UUID,
        amount: Optional[float] = None,
        currency: str = "INR",
        receipt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a Razorpay order"""
        client = RazorpayPaymentProcessor._get_client()

        # Get invoice
        invoice = await PaymentService.get_invoice(db, invoice_id, current_user.practice_id)
        if not invoice:
            raise ValueError("Invoice not found")

        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Invoice is already paid")

        try:
            # Calculate amount in paise
            order_amount = amount or float(invoice.balance_due)
            amount_paise = int(order_amount * 100)

            # Create Razorpay order
            order = client.order.create({
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt or f"invoice_{invoice.id}",
                "payment_capture": 1,  # Auto-capture
                "notes": {
                    "invoice_id": str(invoice.id),
                    "patient_id": str(invoice.patient_id),
                    "practice_id": str(current_user.practice_id),
                },
            })

            logger.info(f"Created Razorpay order: {order['id']}")

            return {
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "receipt": order["receipt"],
                "key_id": settings.RAZORPAY_KEY_ID,
                "status": order["status"],
            }

        except Exception as e:
            logger.error(f"Razorpay order creation error: {str(e)}")
            raise

    @staticmethod
    async def verify_payment(
        db: AsyncSession,
        invoice_id: UUID,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> Dict[str, Any]:
        """Verify a Razorpay payment signature"""
        client = RazorpayPaymentProcessor._get_client()

        try:
            # Verify payment signature
            params = f"{razorpay_order_id}|{razorpay_payment_id}"
            expected_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                params.encode(),
                hashlib.sha256,
            ).hexdigest()

            if expected_signature != razorpay_signature:
                raise ValueError("Invalid payment signature")

            # Fetch payment details from Razorpay
            payment = client.payment.fetch(razorpay_payment_id)

            # Mark invoice as paid
            invoice = await PaymentService.mark_invoice_paid(db, invoice_id)
            if not invoice:
                raise ValueError("Invoice not found")

            # Create payment record
            payment_record = await PaymentService.create_payment_record(
                db=db,
                invoice_id=invoice.id,
                patient_id=invoice.patient_id,
                amount=float(payment["amount"] / 100),  # Convert paise to INR
                payment_method=payment.get("method", "upi"),
                transaction_id=razorpay_payment_id,
                status=PaymentStatus.COMPLETED,
                notes=f"Razorpay payment: {razorpay_payment_id}",
            )

            logger.info(f"Verified Razorpay payment: {razorpay_payment_id}")

            return {
                "payment_id": razorpay_payment_id,
                "order_id": razorpay_order_id,
                "amount": float(payment["amount"] / 100),
                "currency": payment.get("currency", "INR"),
                "status": "captured",
                "method": payment.get("method", "upi"),
            }

        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            raise

    @staticmethod
    async def process_refund(
        db: AsyncSession,
        payment_id: str,
        amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Process a Razorpay refund"""
        client = RazorpayPaymentProcessor._get_client()

        try:
            # Find the payment
            payment = await PaymentService.get_payment(db, payment_id)
            if not payment:
                raise ValueError("Payment not found")

            # Process refund
            refund_params = {"payment_id": payment_id}
            if amount:
                refund_params["amount"] = int(amount * 100)  # Convert to paise

            refund = client.refund.create(refund_params)

            # Update payment status
            await PaymentService.update_payment_status(
                db, payment.id, PaymentStatus.REFUNDED
            )

            logger.info(f"Processed Razorpay refund: {refund['id']}")

            return {
                "refund_id": refund["id"],
                "amount": float(refund["amount"] / 100),
                "status": refund["status"],
            }

        except Exception as e:
            logger.error(f"Razorpay refund error: {str(e)}")
            raise


class WebhookProcessor:
    """Handles payment webhook processing"""

    @staticmethod
    def verify_stripe_signature(
        payload: bytes,
        sig_header: str,
    ) -> Dict[str, Any]:
        """Verify and parse Stripe webhook"""
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise ValueError("Stripe webhook secret not configured")

        try:
            event = stripe_lib.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe_lib.error.SignatureVerificationError:
            raise ValueError("Invalid signature")

    @staticmethod
    def verify_razorpay_signature(
        body: bytes,
        signature: str,
    ) -> Dict[str, Any]:
        """Verify and parse Razorpay webhook"""
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            raise ValueError("Razorpay webhook secret not configured")

        expected_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        if signature != expected_signature:
            raise ValueError("Invalid webhook signature")

        payload = json.loads(body)
        return payload
