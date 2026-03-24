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
