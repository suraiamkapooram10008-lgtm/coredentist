"""
Billing Service - Business Logic
Handles invoice generation, payment processing, and billing calculations
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus, PaymentMethod
from app.schemas.billing import InvoiceCreate


class BillingService:
    """Service for managing billing and invoices"""

    @staticmethod
    def create_invoice(
        db: Session,
        invoice_data: InvoiceCreate,
        practice_id: int,
        created_by_id: int
    ) -> Invoice:
        """Create a new invoice with line items"""
        
        # Calculate totals from line items
        subtotal = Decimal("0.00")
        # Prefer line_items (already converted to dicts by schema), fallback to items
        raw_items = invoice_data.line_items
        if not raw_items and invoice_data.items:
            raw_items = []
            for item in invoice_data.items:
                if hasattr(item, 'model_dump'):
                    raw_items.append(item.model_dump())
                elif hasattr(item, 'dict'):
                    raw_items.append(item.dict())
                elif isinstance(item, dict):
                    raw_items.append(item)
        items = raw_items or []
        for item in items:
            qty = Decimal(str(item.get("quantity", 1)))
            price = Decimal(str(item.get("unit_price", 0)))
            item_total = qty * price
            subtotal += item_total
        
        # Calculate tax if applicable
        tax_rate_val = getattr(invoice_data, 'tax_rate', None) or 0
        tax_rate = Decimal(str(tax_rate_val))
        tax_amount = subtotal * tax_rate / Decimal("100")
        
        # Calculate total
        total_amount = subtotal + tax_amount
        
        # Build line_items dicts
        line_items_dicts = [
            {
                "description": item.get("description", ""),
                "quantity": float(item.get("quantity", 1)),
                "unit_price": float(item.get("unit_price", 0)),
                "total": float(Decimal(str(item.get("quantity", 1))) * Decimal(str(item.get("unit_price", 0)))),
                "procedure_code": item.get("procedure_code", None)
            }
            for item in items
        ]
        
        # Create invoice
        invoice = Invoice(
            patient_id=invoice_data.patient_id,
            practice_id=practice_id,
            invoice_number=BillingService._generate_invoice_number(db, practice_id),
            due_date=invoice_data.due_date,
            subtotal=subtotal,
            tax=tax_amount,
            total=total_amount,
            amount_paid=Decimal("0.00"),
            balance_due=total_amount,
            status=InvoiceStatus.DRAFT,
            notes=invoice_data.notes,
            line_items=line_items_dicts
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        return invoice

    @staticmethod
    def _generate_invoice_number(db: Session, practice_id: int) -> str:
        """Generate unique invoice number"""
        
        # Get the last invoice number for this practice
        last_invoice = db.query(Invoice).filter(
            Invoice.practice_id == practice_id
        ).order_by(Invoice.id.desc()).first()
        
        if last_invoice and last_invoice.invoice_number:
            # Extract number from format INV-YYYY-NNNN
            try:
                parts = last_invoice.invoice_number.split('-')
                if len(parts) == 3:
                    last_number = int(parts[2])
                    next_number = last_number + 1
                else:
                    next_number = 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        year = datetime.utcnow().year
        return f"INV-{year}-{next_number:04d}"

    @staticmethod
    def update_invoice_status(
        db: Session,
        invoice_id: int,
        new_status: InvoiceStatus,
        practice_id: int
    ) -> Invoice:
        """Update invoice status"""
        
        invoice = db.query(Invoice).filter(
            and_(
                Invoice.id == invoice_id,
                Invoice.practice_id == practice_id
            )
        ).first()
        
        if not invoice:
            raise ValueError("Invoice not found")
        
        # Validate status transition
        valid_transitions = {
            InvoiceStatus.DRAFT: [InvoiceStatus.SENT, InvoiceStatus.PENDING, InvoiceStatus.VOIDED],
            InvoiceStatus.PENDING: [InvoiceStatus.SENT, InvoiceStatus.PAID, InvoiceStatus.OVERDUE, InvoiceStatus.VOIDED],
            InvoiceStatus.SENT: [InvoiceStatus.PAID, InvoiceStatus.OVERDUE, InvoiceStatus.VOIDED],
            InvoiceStatus.OVERDUE: [InvoiceStatus.PAID, InvoiceStatus.VOIDED],
            InvoiceStatus.PAID: [],
            InvoiceStatus.VOIDED: [],
            InvoiceStatus.CANCELLED: []
        }
        
        if new_status not in valid_transitions.get(invoice.status, []):
            raise ValueError(
                f"Invalid status transition from {invoice.status} to {new_status}"
            )
        
        invoice.status = new_status
        invoice.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(invoice)
        
        return invoice

    @staticmethod
    def record_payment(
        db: Session,
        invoice_id: int,
        amount: Decimal,
        payment_method: PaymentMethod,
        practice_id: int,
        transaction_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Payment:
        """Record a payment against an invoice"""
        
        invoice = db.query(Invoice).filter(
            and_(
                Invoice.id == invoice_id,
                Invoice.practice_id == practice_id
            )
        ).first()
        
        if not invoice:
            raise ValueError("Invoice not found")
        
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        if amount > invoice.balance_due:
            raise ValueError("Payment amount exceeds balance due")
        
        # Create payment record
        payment = Payment(
            invoice_id=invoice_id,
            patient_id=invoice.patient_id,
            practice_id=practice_id,
            amount=amount,
            payment_method=payment_method,
            payment_date=datetime.utcnow(),
            transaction_id=transaction_id,
            status=PaymentStatus.COMPLETED,
            notes=notes
        )
        
        db.add(payment)
        
        # Update invoice
        invoice.amount_paid += amount
        invoice.balance_due -= amount
        invoice.updated_at = datetime.utcnow()
        
        # Update invoice status if fully paid
        if invoice.balance_due == 0:
            invoice.status = InvoiceStatus.PAID
        
        db.commit()
        db.refresh(payment)
        
        return payment

    @staticmethod
    def get_billing_summary(
        db: Session,
        practice_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get billing summary for a practice"""
        
        query = db.query(Invoice).filter(Invoice.practice_id == practice_id)
        
        if start_date:
            query = query.filter(Invoice.created_at >= start_date)
        
        if end_date:
            query = query.filter(Invoice.created_at < end_date)
        
        invoices = query.all()
        
        total_billed = sum(inv.total for inv in invoices)
        total_paid = sum(inv.amount_paid for inv in invoices)
        total_outstanding = sum(inv.balance_due for inv in invoices)
        
        # Count by status
        status_counts = {}
        for status in InvoiceStatus:
            count = sum(1 for inv in invoices if inv.status == status)
            status_counts[status.value] = count
        
        # Calculate overdue invoices
        overdue_invoices = [
            inv for inv in invoices
            if inv.due_date and inv.due_date < datetime.utcnow().date() and inv.balance_due > 0
        ]
        total_overdue = sum(inv.balance_due for inv in overdue_invoices)
        
        return {
            "total_invoices": len(invoices),
            "total_billed": float(total_billed),
            "total_paid": float(total_paid),
            "total_outstanding": float(total_outstanding),
            "total_overdue": float(total_overdue),
            "overdue_count": len(overdue_invoices),
            "status_breakdown": status_counts,
            "collection_rate": float(total_paid / total_billed * 100) if total_billed > 0 else 0
        }

    @staticmethod
    def get_patient_balance(
        db: Session,
        patient_id: int,
        practice_id: int
    ) -> Dict[str, Any]:
        """Get total balance for a patient"""
        
        invoices = db.query(Invoice).filter(
            and_(
                Invoice.patient_id == patient_id,
                Invoice.practice_id == practice_id,
                Invoice.status != InvoiceStatus.VOIDED
            )
        ).all()
        
        total_balance = sum(inv.balance_due for inv in invoices)
        total_billed = sum(inv.total for inv in invoices)
        total_paid = sum(inv.amount_paid for inv in invoices)
        
        overdue_invoices = [
            inv for inv in invoices
            if inv.due_date and inv.due_date < datetime.utcnow().date() and inv.balance_due > 0
        ]
        overdue_balance = sum(inv.balance_due for inv in overdue_invoices)
        
        return {
            "patient_id": patient_id,
            "total_balance": float(total_balance),
            "total_billed": float(total_billed),
            "total_paid": float(total_paid),
            "overdue_balance": float(overdue_balance),
            "invoice_count": len(invoices),
            "overdue_count": len(overdue_invoices)
        }

    @staticmethod
    def mark_overdue_invoices(db: Session, practice_id: int) -> int:
        """Mark invoices as overdue if past due date"""
        
        now = datetime.utcnow().date()
        
        overdue_invoices = db.query(Invoice).filter(
            and_(
                Invoice.practice_id == practice_id,
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PENDING]),
                Invoice.due_date < now,
                Invoice.balance_due > 0
            )
        ).all()
        
        count = 0
        for invoice in overdue_invoices:
            invoice.status = InvoiceStatus.OVERDUE
            invoice.updated_at = datetime.utcnow()
            count += 1
        
        if count > 0:
            db.commit()
        
        return count

    @staticmethod
    def void_invoice(
        db: Session,
        invoice_id: int,
        practice_id: int,
        reason: Optional[str] = None
    ) -> Invoice:
        """Void an invoice"""
        
        invoice = db.query(Invoice).filter(
            and_(
                Invoice.id == invoice_id,
                Invoice.practice_id == practice_id
            )
        ).first()
        
        if not invoice:
            raise ValueError("Invoice not found")
        
        if invoice.amount_paid > 0:
            raise ValueError("Cannot void invoice with payments. Refund payments first.")
        
        invoice.status = InvoiceStatus.VOIDED
        invoice.notes = f"{invoice.notes or ''}\nVoided: {reason or 'No reason provided'}"
        invoice.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(invoice)
        
        return invoice
