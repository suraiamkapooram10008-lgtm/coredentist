"""
Payment Reconciliation Service
Handles payment reconciliation, recurring revenue, and dashboard data
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus
from app.models.payment import RecurringBilling, RecurringStatus

logger = logging.getLogger(__name__)


class PaymentReconciliationService:
    """Service for payment reconciliation and reporting"""
    
    @staticmethod
    async def get_recurring_revenue(
        db: AsyncSession,
        practice_id: UUID,
    ) -> float:
        """Calculate monthly recurring revenue (MRR)"""
        try:
            result = await db.execute(
                select(RecurringBilling).where(
                    RecurringBilling.practice_id == practice_id,
                    RecurringBilling.status == RecurringStatus.ACTIVE,
                )
            )
            recurring_plans = result.scalars().all()
            
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
            
            logger.info(f"Calculated MRR for practice {practice_id}: {recurring_revenue}")
            return round(recurring_revenue, 2)
            
        except Exception as e:
            logger.error(f"Error calculating recurring revenue: {str(e)}")
            return 0.0
    
    @staticmethod
    async def get_payment_methods_status(
        db: AsyncSession,
        practice_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get available payment methods for the practice"""
        from app.core.config_simple import settings
        
        methods = []
        
        # Check Stripe
        if settings.STRIPE_API_KEY:
            methods.append({
                "type": "card",
                "name": "Credit/Debit Card",
                "enabled": True,
                "provider": "stripe",
            })
        
        # Check Razorpay
        if settings.RAZORPAY_KEY_ID:
            methods.append({
                "type": "upi",
                "name": "UPI",
                "enabled": True,
                "provider": "razorpay",
            })
            methods.append({
                "type": "netbanking",
                "name": "Net Banking",
                "enabled": True,
                "provider": "razorpay",
            })
            methods.append({
                "type": "wallet",
                "name": "Digital Wallets",
                "enabled": True,
                "provider": "razorpay",
            })
        
        return methods
    
    @staticmethod
    async def get_payment_terminals(
        db: AsyncSession,
        practice_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get payment terminals configured for the practice"""
        from app.core.config_simple import settings
        
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
        
        return terminals
    
    @staticmethod
    async def get_recurring_plans(
        db: AsyncSession,
        practice_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get recurring payment plans for the practice"""
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
        return plans
    
    @staticmethod
    async def reconcile_payments(
        db: AsyncSession,
        practice_id: UUID,
    ) -> Dict[str, Any]:
        """Reconcile payments and generate reconciliation report"""
        try:
            # Get all payments for the practice
            result = await db.execute(
                select(Payment)
                .join(Invoice)
                .where(Invoice.practice_id == practice_id)
                .order_by(Payment.created_at.desc())
            )
            payments = result.scalars().all()
            
            # Calculate totals by status
            completed_total = sum(
                float(p.amount) for p in payments if p.status == PaymentStatus.COMPLETED
            )
            failed_total = sum(
                float(p.amount) for p in payments if p.status == PaymentStatus.FAILED
            )
            refunded_total = sum(
                float(p.amount) for p in payments if p.status == PaymentStatus.REFUNDED
            )
            pending_total = sum(
                float(p.amount) for p in payments if p.status == PaymentStatus.PENDING
            )
            
            # Calculate by payment method
            payment_methods = {}
            for payment in payments:
                method = payment.payment_method or "unknown"
                if method not in payment_methods:
                    payment_methods[method] = {
                        "count": 0,
                        "total": 0.0,
                        "completed": 0.0,
                        "failed": 0.0,
                    }
                
                payment_methods[method]["count"] += 1
                payment_methods[method]["total"] += float(payment.amount)
                
                if payment.status == PaymentStatus.COMPLETED:
                    payment_methods[method]["completed"] += float(payment.amount)
                elif payment.status == PaymentStatus.FAILED:
                    payment_methods[method]["failed"] += float(payment.amount)
            
            logger.info(f"Reconciled payments for practice {practice_id}")
            
            return {
                "total_payments": len(payments),
                "completed_total": round(completed_total, 2),
                "failed_total": round(failed_total, 2),
                "refunded_total": round(refunded_total, 2),
                "pending_total": round(pending_total, 2),
                "payment_methods": payment_methods,
            }
            
        except Exception as e:
            logger.error(f"Error reconciling payments: {str(e)}")
            return {
                "total_payments": 0,
                "completed_total": 0.0,
                "failed_total": 0.0,
                "refunded_total": 0.0,
                "pending_total": 0.0,
                "payment_methods": {},
            }
