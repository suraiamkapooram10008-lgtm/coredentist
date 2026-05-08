"""
Billing Endpoints
CRUD operations for invoices and payments
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, and_, func
from datetime import datetime, date, timezone, timedelta
from typing import List, Optional, Any
from decimal import Decimal
from uuid import UUID
import uuid

from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from app.api.deps import get_current_user, require_role, verify_csrf
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
from app.models.billing import (
    Invoice, Payment, InvoiceStatus, PaymentMethod, PaymentStatus,
    PaymentPlan, PaymentPlanInstallment, PaymentPlanStatus
)
from app.models.patient import Patient
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
    BillingSummary,
)

router = APIRouter()


# Invoice Endpoints

@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    patient_id: Optional[uuid.UUID] = Query(None, description="Filter by patient"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List invoices with optional filters
    """
    query = (
        select(Invoice)
        .where(Invoice.practice_id == current_user.practice_id)
        .options(joinedload(Invoice.patient))
    )
    
    if status:
        query = query.where(Invoice.status == status)
    if patient_id:
        query = query.where(Invoice.patient_id == patient_id)
    if start_date:
        query = query.where(func.date(Invoice.created_at) >= start_date)
    if end_date:
        query = query.where(func.date(Invoice.created_at) <= end_date)
    
    query = query.order_by(Invoice.created_at.desc())
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    await log_audit_event(db, current_user, "list_invoices", "invoice", None, request)
    await db.commit()
    
    return InvoiceListResponse(invoices=invoices, count=len(invoices))


@router.get("/invoices/outstanding", response_model=InvoiceListResponse)
async def get_outstanding_invoices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get all outstanding (unpaid) invoices"""
    query = (
        select(Invoice)
        .where(
            Invoice.practice_id == current_user.practice_id,
            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.SENT, InvoiceStatus.OVERDUE]),
            Invoice.balance_due > 0
        )
        .order_by(Invoice.due_date)
    )
    result = await db.execute(query)
    invoices = result.scalars().all()
    return InvoiceListResponse(invoices=invoices, count=len(invoices))


@router.get("/invoices/overdue", response_model=InvoiceListResponse)
async def get_overdue_invoices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get all overdue invoices"""
    today = date.today()
    query = (
        select(Invoice)
        .where(
            Invoice.practice_id == current_user.practice_id,
            Invoice.due_date < today,
            Invoice.status != InvoiceStatus.PAID,
            Invoice.balance_due > 0
        )
        .order_by(Invoice.due_date)
    )
    result = await db.execute(query)
    invoices = result.scalars().all()
    return InvoiceListResponse(invoices=invoices, count=len(invoices))


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get invoice by ID
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.practice_id == current_user.practice_id,
        )
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    
    await log_audit_event(db, current_user, "view_invoice", "invoice", invoice.id, request)
    await db.commit()
    
    return invoice


@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    invoice_data: InvoiceCreate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new invoice
    """
    result = await db.execute(
        select(Patient).where(
            Patient.id == invoice_data.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    today = datetime.now(timezone.utc)
    invoice_count_result = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.practice_id == current_user.practice_id,
            func.date(Invoice.created_at) == today.date()
        )
    )
    count = invoice_count_result.scalar() or 0
    import uuid as uuid_lib
    invoice_number = f"INV-{today.strftime('%Y%m%d')}-{count + 1:04d}-{str(uuid_lib.uuid4())[:8]}"
    
    # Calculate total from provided values
    subtotal = invoice_data.subtotal or Decimal("0.00")
    tax = invoice_data.tax or Decimal("0.00")
    discount = invoice_data.discount or Decimal("0.00")
    total = subtotal + tax - discount
    
    invoice = Invoice(
        practice_id=current_user.practice_id,
        patient_id=invoice_data.patient_id,
        invoice_number=invoice_number,
        status=InvoiceStatus.PENDING,
        subtotal=subtotal,
        tax=tax,
        total=total,
        amount_paid=Decimal("0.00"),
        balance_due=total,
        line_items=invoice_data.line_items,
        due_date=invoice_data.due_date,
        notes=invoice_data.notes,
    )
    
    db.add(invoice)
    await log_audit_event(db, current_user, "create_invoice", "invoice", None, request)
    await db.commit()
    await db.refresh(invoice)
    
    return invoice


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: uuid.UUID,
    invoice_data: InvoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update invoice
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.practice_id == current_user.practice_id,
        )
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    update_data = invoice_data.dict(exclude_unset=True)
    
    if 'line_items' in update_data or 'tax_rate' in update_data:
        line_items = update_data.get('line_items', invoice.line_items)
        tax_rate = update_data.get('tax_rate', Decimal('0.0'))
        
        subtotal = sum(item['total'] for item in line_items)
        tax = subtotal * tax_rate
        total = subtotal + tax
        
        invoice.subtotal = subtotal
        invoice.tax = tax
        invoice.total = total
        invoice.line_items = line_items
    
    for field, value in update_data.items():
        if field not in ['line_items', 'tax_rate']:
            setattr(invoice, field, value)
    
    await db.commit()
    await db.refresh(invoice)
    
    return invoice


@router.delete("/invoices/{invoice_id}")
async def delete_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete invoice (soft delete by cancelling)
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.practice_id == current_user.practice_id,
        )
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    invoice.status = InvoiceStatus.CANCELLED
    await db.commit()
    
    return {"message": "Invoice cancelled successfully"}


# Payment Endpoints

@router.get("/payments", response_model=PaymentListResponse)
async def list_payments(
    invoice_id: Optional[uuid.UUID] = Query(None),
    patient_id: Optional[uuid.UUID] = Query(None),
    status: Optional[PaymentStatus] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List payments
    """
    query = (
        select(Payment)
        .join(Invoice)
        .where(Invoice.practice_id == current_user.practice_id)
        .options(joinedload(Payment.invoice), joinedload(Payment.patient))
    )
    
    if invoice_id:
        query = query.where(Payment.invoice_id == invoice_id)
    if patient_id:
        query = query.where(Payment.patient_id == patient_id)
    if status:
        query = query.where(Payment.status == status)
    if start_date:
        query = query.where(func.date(Payment.created_at) >= start_date)
    if end_date:
        query = query.where(func.date(Payment.created_at) <= end_date)
    
    query = query.order_by(Payment.created_at.desc())
    result = await db.execute(query)
    payments = result.scalars().all()
    
    await log_audit_event(db, current_user, "list_payments", "payment", None, request)
    await db.commit()
    
    return PaymentListResponse(payments=payments, count=len(payments))


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: uuid.UUID,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get payment by ID
    """
    result = await db.execute(
        select(Payment).join(Invoice).where(
            Payment.id == payment_id,
            Invoice.practice_id == current_user.practice_id,
        )
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    await log_audit_event(db, current_user, "view_payment", "payment", payment.id, request)
    await db.commit()
    
    return payment


@router.post("/payments", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new payment
    CRIT-27 FIX: Verify patient ownership
    """
    # 1. Validate amount is positive
    if payment_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero"
        )
    
    # 2. Verify patient belongs to practice (CRIT-27)
    patient_res = await db.execute(
        select(Patient.id).where(
            Patient.id == payment_data.patient_id,
            Patient.practice_id == current_user.practice_id
        )
    )
    if not patient_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # 3. Get invoice and verify ownership
    invoice = None
    if payment_data.invoice_id:
        result = await db.execute(
            select(Invoice).where(
                Invoice.id == payment_data.invoice_id,
                Invoice.practice_id == current_user.practice_id,
            )
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        
        # Verify invoice belongs to the SAME patient
        if invoice.patient_id != payment_data.patient_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice does not belong to this patient")
    
    # Generate payment number
    today = datetime.now(timezone.utc)
    payment_count_result = await db.execute(
        select(func.count(Payment.id)).where(
            func.date(Payment.created_at) == today.date()
        )
    )
    count = payment_count_result.scalar() or 0
    payment_number = f"PAY-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    
    payment = Payment(
        practice_id=current_user.practice_id,
        invoice_id=payment_data.invoice_id,
        patient_id=payment_data.patient_id,
        payment_number=payment_number,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        payment_date=payment_data.payment_date or today.date(),
        transaction_id=payment_data.reference_number,
        reference_number=payment_data.reference_number,
        status=PaymentStatus.COMPLETED,
        notes=payment_data.notes,
    )
    
    db.add(payment)
    
    # Update invoice balance (CRIT-28)
    if invoice:
        invoice.amount_paid = (invoice.amount_paid or Decimal("0.00")) + payment_data.amount
        invoice.balance_due = invoice.total - invoice.amount_paid
        
        if invoice.balance_due <= 0:
            invoice.status = InvoiceStatus.PAID
    
    # HIPAA: Log payment creation
    await log_audit_event(db, current_user, "create_payment", "payment", None, request)
    await db.commit()
    await db.refresh(payment)
    
    return payment


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: uuid.UUID,
    refund_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Refund a payment (full or partial)
    """
    result = await db.execute(
        select(Payment).join(Invoice).where(
            Payment.id == payment_id,
            Invoice.practice_id == current_user.practice_id,
        )
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    
    if payment.status == PaymentStatus.REFUNDED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment already refunded")
    
    refund_amount = Decimal(str(refund_data.get("amount", payment.amount)))
    
    if refund_amount > payment.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund amount exceeds payment amount")
    
    # Update payment
    payment.refunded_amount = refund_amount
    payment.refunded_at = datetime.now(timezone.utc)
    
    if refund_amount == payment.amount:
        payment.status = PaymentStatus.REFUNDED
    else:
        payment.status = PaymentStatus.PARTIALLY_REFUNDED
    
    # Update invoice
    if payment.invoice_id:
        result = await db.execute(select(Invoice).where(Invoice.id == payment.invoice_id))
        invoice = result.scalar_one_or_none()
        if invoice:
            invoice.amount_paid = (invoice.amount_paid or Decimal("0.00")) - refund_amount
            invoice.balance_due = invoice.total - invoice.amount_paid
            if invoice.status == InvoiceStatus.PAID:
                invoice.status = InvoiceStatus.PENDING
    
    await db.commit()
    await db.refresh(payment)
    
    return payment


@router.get("/summary", response_model=BillingSummary)
async def get_billing_summary(
    request: Request,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get billing summary
    """
    date_filter = []
    if start_date:
        date_filter.append(func.date(Invoice.created_at) >= start_date)
    if end_date:
        date_filter.append(func.date(Invoice.created_at) <= end_date)
    
    invoice_query = select(
        func.count(Invoice.id).label('total_invoices'),
        func.sum(Invoice.total).label('total_revenue'),
        func.sum(Invoice.tax).label('total_tax'),
    ).where(Invoice.practice_id == current_user.practice_id, *date_filter)
    
    invoice_result = await db.execute(invoice_query)
    invoice_stats = invoice_result.first()
    
    payment_query = select(
        func.count(Payment.id).label('total_payments'),
        func.sum(Payment.amount).label('total_collected'),
    ).join(Invoice).where(Invoice.practice_id == current_user.practice_id, *date_filter)
    
    payment_result = await db.execute(payment_query)
    payment_stats = payment_result.first()
    
    status_query = select(
        Invoice.status,
        func.count(Invoice.id).label('count'),
        func.sum(Invoice.total).label('amount'),
    ).where(Invoice.practice_id == current_user.practice_id, *date_filter).group_by(Invoice.status)
    
    status_result = await db.execute(status_query)
    status_breakdown = status_result.all()
    
    await log_audit_event(db, current_user, "view_billing_summary", "practice", current_user.practice_id, request)
    await db.commit()
    
    return BillingSummary(
        total_invoices=invoice_stats.total_invoices or 0,
        total_revenue=float(invoice_stats.total_revenue or 0),
        total_tax=float(invoice_stats.total_tax or 0),
        total_payments=payment_stats.total_payments or 0,
        total_collected=float(payment_stats.total_collected or 0),
        outstanding_balance=float((invoice_stats.total_revenue or 0) - (payment_stats.total_collected or 0)),
        status_breakdown=[
            {"status": status, "count": count, "amount": float(amount or 0)}
            for status, count, amount in status_breakdown
        ],
    )


@router.post("/invoices/{invoice_id}/send")
async def send_invoice_email(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Send invoice via email to patient
    """
    result = await db.execute(
        select(Invoice).options(joinedload(Invoice.patient)).where(
            Invoice.id == invoice_id,
            Invoice.practice_id == current_user.practice_id,
        )
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    # Update status to sent
    invoice.status = InvoiceStatus.SENT
    await db.commit()
    
    # CRIT-05 FIX: Actually send invoice email to patient
    from app.core.email import email_service
    from datetime import datetime
    
    # Build invoice items from line items
    items = []
    for item in invoice.line_items or []:
        items.append({
            "description": item.get("description", ""),
            "quantity": item.get("quantity", 1),
            "unit_price": float(item.get("unit_price", 0)),
            "total": float(item.get("total", 0)),
        })
    
    try:
        await email_service.send_invoice_email(
            to=invoice.patient.email,
            patient_name=invoice.patient.first_name,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.created_at.strftime("%Y-%m-%d") if invoice.created_at else datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            due_date=invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "Upon Receipt",
            amount_due=float(invoice.total_amount),
            items=items,
            practice_name="CoreDent",  # Could be fetched from practice settings
        )
    except Exception as e:
        # Log error but don't fail the request - invoice status was already updated
        import logging
        logging.getLogger(__name__).error(f"Failed to send invoice email: {e}")
    
    return {"message": "Invoice sent successfully", "invoice_id": str(invoice.id)}


@router.post("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_as_paid(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Mark invoice as paid (manual payment recording)
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.practice_id == current_user.practice_id,
        )
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice already paid")
    
    # Mark as paid - status change only
    # amount_paid and balance_due are calculated properties based on payments
    invoice.status = InvoiceStatus.PAID
    
    await db.commit()
    
    return {"message": "Invoice marked as paid", "invoice_id": str(invoice.id)}


@router.post("/invoices/{invoice_id}/void")
async def void_invoice(
    invoice_id: uuid.UUID,
    void_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Void an invoice
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.practice_id == current_user.practice_id,
        )
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot void paid invoice")
    
    # Void invoice
    invoice.status = InvoiceStatus.VOIDED
    if void_data.get("reason"):
        invoice.notes = f"{invoice.notes or ''}\nVoided: {void_data['reason']}"
    
    await db.commit()
    
    return {"message": "Invoice voided successfully", "invoice_id": str(invoice.id)}


@router.get("/patients/{patient_id}/summary")
async def get_patient_billing_summary(
    patient_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get billing summary for a specific patient
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # Get invoice stats
    invoice_query = select(
        func.count(Invoice.id).label('total_invoices'),
        func.sum(Invoice.total).label('total_billed'),
        func.sum(Invoice.balance_due).label('outstanding_balance'),
    ).where(Invoice.patient_id == patient_id)
    
    invoice_result = await db.execute(invoice_query)
    invoice_stats = invoice_result.first()
    
    # Get payment stats
    payment_query = select(
        func.count(Payment.id).label('total_payments'),
        func.sum(Payment.amount).label('total_paid'),
    ).where(Payment.patient_id == patient_id)
    
    payment_result = await db.execute(payment_query)
    payment_stats = payment_result.first()
    
    return {
        "patient_id": str(patient_id),
        "total_invoices": invoice_stats.total_invoices or 0,
        "total_billed": float(invoice_stats.total_billed or 0),
        "outstanding_balance": float(invoice_stats.outstanding_balance or 0),
        "total_payments": payment_stats.total_payments or 0,
        "total_paid": float(payment_stats.total_paid or 0),
    }


@router.get("/patients/{patient_id}/payment-methods")
async def list_payment_methods(
    patient_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List payment methods for a patient
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # TODO: Implement payment method storage
    return {"payment_methods": [], "message": "Payment method storage not yet implemented"}


@router.post("/patients/{patient_id}/payment-methods")
async def add_payment_method(
    patient_id: uuid.UUID,
    payment_method_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Add a payment method for a patient
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # TODO: Implement payment method storage
    return {"message": "Payment method storage not yet implemented"}


@router.delete("/patients/{patient_id}/payment-methods/{method_id}")
async def delete_payment_method(
    patient_id: uuid.UUID,
    method_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete a payment method
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    
    # TODO: Implement payment method storage
    return {"message": "Payment method deleted"}


# --- Payment Plan Endpoints ---

@router.post("/payment-plans/", response_model=Any)
async def create_payment_plan(
    plan_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create a new installment-based payment plan
    """
    plan = PaymentPlan(
        practice_id=current_user.practice_id,
        patient_id=UUID(plan_data.get('patient_id')),
        invoice_id=UUID(plan_data.get('invoice_id')) if plan_data.get('invoice_id') else None,
        total_amount=Decimal(str(plan_data.get('total_amount'))),
        initial_deposit=Decimal(str(plan_data.get('initial_deposit', 0))),
        start_date=datetime.now(timezone.utc).date(),
        notes=plan_data.get('notes'),
    )
    db.add(plan)
    await db.flush()
    
    num_months = int(plan_data.get('months', 12))
    installment_amount = (plan.total_amount - plan.initial_deposit) / num_months
    
    for i in range(num_months):
        installment = PaymentPlanInstallment(
            plan_id=plan.id,
            amount=installment_amount,
            due_date=(datetime.now(timezone.utc) + timedelta(days=30*(i+1))).date(),
            status="scheduled"
        )
        db.add(installment)
    
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/payment-plans", response_model=List[Any])
async def list_payment_plans(
    patient_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all payment plans for the practice
    """
    query = select(PaymentPlan).where(PaymentPlan.practice_id == current_user.practice_id)
    if patient_id:
        query = query.where(PaymentPlan.patient_id == patient_id)
    
    result = await db.execute(query.options(joinedload(PaymentPlan.installments)))
    return result.scalars().unique().all()