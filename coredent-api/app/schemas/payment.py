"""
Payment Schemas
Stripe payment request/response models
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class PaymentIntentCreate(BaseModel):
    """Request to create a Stripe PaymentIntent"""
    invoice_id: UUID
    amount: Optional[float] = Field(
        None,
        description="Amount to charge. If not provided, uses invoice balance."
    )


class PaymentIntentResponse(BaseModel):
    """Response from creating a PaymentIntent"""
    client_secret: str
    payment_intent_id: str
    amount: float
    currency: str


class PaymentMethodAttach(BaseModel):
    """Request to attach a payment method to a customer"""
    customer_id: str
    payment_method_id: str


class PaymentWebhookEvent(BaseModel):
    """Stripe webhook event"""
    type: str
    data: dict


# ============================================
# Razorpay Schemas (Indian Market - UPI/Paytm/PhonePe)
# ============================================

class RazorpayOrderCreate(BaseModel):
    """Request to create a Razorpay Order"""
    invoice_id: UUID
    amount: Optional[float] = Field(
        None,
        description="Amount in INR. If not provided, uses invoice balance."
    )
    currency: str = Field(default="INR", description="Currency (default: INR)")
    receipt: Optional[str] = Field(None, description="Custom receipt ID")


class RazorpayOrderResponse(BaseModel):
    """Response from creating a Razorpay Order"""
    order_id: str
    amount: int  # Amount in paise (smallest currency unit)
    currency: str
    receipt: str
    key_id: str  # Razorpay key_id for frontend SDK
    status: str


class RazorpayPaymentVerify(BaseModel):
    """Request to verify a Razorpay Payment"""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    invoice_id: UUID


class RazorpayPaymentResponse(BaseModel):
    """Response from verifying a Razorpay Payment"""
    payment_id: str
    order_id: str
    amount: float
    currency: str
    status: str
    method: str  # upi, card, netbanking, wallet


class RazorpayRefundRequest(BaseModel):
    """Request to refund a Razorpay Payment"""
    payment_id: str
    amount: Optional[float] = Field(None, description="Partial refund amount. If not provided, full refund.")


class RazorpayRefundResponse(BaseModel):
    """Response from processing a Razorpay Refund"""
    refund_id: str
    amount: float
    status: str


class RazorpayWebhookEvent(BaseModel):
    """Razorpay webhook event"""
    event: str
    payload: dict
