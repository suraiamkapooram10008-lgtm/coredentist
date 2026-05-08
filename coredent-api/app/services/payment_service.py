"""
Payment Service
Core business logic for payment operations
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus
from app.models.patient import Patient

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for payment operations"""
    
    @staticmethod
    async def get_invoice(
        db: AsyncSession,
        invoice_id: UUID,
        practice_id: Optional[UUID] = None,
    ) -> Optional[Invoice]:
        """Get an invoice"""
        query = select(Invoice).where(Invoice.id == invoice_id)
        
        if practice_id:
            query = query.where(Invoice.practice_id == practice_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_payment(
        db: AsyncSession,
        transaction_id: str,
    ) -> Optional[Payment]:
        """Get a payment by transaction ID"""
        result = await db.execute(
            select(Payment).where(Payment.transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_payment_record(
        db: AsyncSession,
        invoice_id: UUID,
        patient_id: UUID,
        amount: float,
        payment_method: str,
        transaction_id: str,
        status: PaymentStatus,
        notes: str = "",
    ) -> Payment:
        """Create a payment record"""
        payment = Payment(
            invoice_id=invoice_id,
            patient_id=patient_id,
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            status=status,
            notes=notes,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        logger.info(f"Created payment record: {payment.id} for invoice {invoice_id}")
        return payment
    
    @staticmethod
    async def mark_invoice_paid(
        db: AsyncSession,
        invoice_id: UUID,
    ) -> Optional[Invoice]:
        """Mark an invoice as paid"""
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            return None
        
        invoice.status = InvoiceStatus.PAID
        invoice.balance_due = 0
        await db.commit()
        await db.refresh(invoice)
        logger.info(f"Marked invoice {invoice_id} as paid")
        return invoice
    
    @staticmethod
    async def update_payment_status(
        db: AsyncSession,
        payment_id: UUID,
        status: PaymentStatus,
    ) -> Optional[Payment]:
        """Update payment status"""
        result = await db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            return None
        
        payment.status = status
        await db.commit()
        await db.refresh(payment)
        logger.info(f"Updated payment {payment_id} status to {status}")
        return payment
    
    @staticmethod
    async def list_payments(
        db: AsyncSession,
        practice_id: UUID,
        status: Optional[PaymentStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[Payment], int]:
        """List payments with filtering and pagination"""
        query = (
            select(Payment)
            .join(Invoice)
            .where(Invoice.practice_id == practice_id)
            .order_by(Payment.created_at.desc())
        )
        
        if status:
            query = query.where(Payment.status == status)
        
        if start_date:
            query = query.where(Payment.created_at >= start_date)
        
        if end_date:
            query = query.where(Payment.created_at <= end_date)
        
        # Get total count
        count_result = await db.execute(
            select(Payment)
            .join(Invoice)
            .where(Invoice.practice_id == practice_id)
        )
        total = len(count_result.scalars().all())
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        payments = result.scalars().all()
        
        return payments, total
    
    @staticmethod
    async def get_payment_stats(
        db: AsyncSession,
        practice_id: UUID,
    ) -> Dict[str, Any]:
        """Get payment statistics for the practice"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        
        # Today's revenue (paid invoices today)
        today_result = await db.execute(
            select(Invoice).where(
                Invoice.practice_id == practice_id,
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
                Invoice.practice_id == practice_id,
                Invoice.status == InvoiceStatus.PAID,
                Invoice.updated_at >= month_start,
            )
        )
        month_invoices = month_result.scalars().all()
        month_revenue = sum(float(inv.total_amount) for inv in month_invoices)
        
        # Last month's revenue for growth calculation
        last_month_result = await db.execute(
            select(Invoice).where(
                Invoice.practice_id == practice_id,
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
                Invoice.practice_id == practice_id,
                Invoice.status == InvoiceStatus.PENDING,
            )
        )
        pending_invoices = pending_result.scalars().all()
        pending_amount = sum(float(inv.balance_due) for inv in pending_invoices)
        pending_count = len(pending_invoices)
        
        return {
            "today_revenue": today_revenue,
            "today_transactions": today_transactions,
            "month_revenue": month_revenue,
            "month_growth": month_growth,
            "pending_amount": pending_amount,
            "pending_count": pending_count,
        }
