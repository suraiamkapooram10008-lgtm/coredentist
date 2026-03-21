"""
Billing Endpoints
CRUD operations for invoices and payments
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, date
from typing import List, Optional, Any
from decimal import Decimal

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.billing import Invoice, Payment, InvoiceStatus, PaymentMethod, PaymentStatus
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
from app.api.deps import verify_csrf

router = APIRouter()


# Invoice Endpoints

@router.get("/invoices/", response_model=InvoiceListResponse)
async def list_invoices(
    status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List invoices with optional filters
    """
    # Build query
    query = select(Invoice).where(Invoice.practice_id == current_user.practice_id)
    
    # Apply filters
    if status:
        query = query.where(Invoice.status == status)
    if patient_id:
        query = query.where(Invoice.patient_id == patient_id)
    if start_date:
        query = query.where(func.date(Invoice.created_at) >= start_date)
    if end_date:
        query = query.where(func.date(Invoice.created_at) <= end_date)
    
    # Order by creation date (newest first)
    query = query.order_by(Invoice.created_at.desc())
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    return InvoiceListResponse(
        invoices=invoices,
        count=len(invoices),
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
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
    
    return invoice


@router.post("/invoices/", response_model=InvoiceResponse)
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new invoice
    """
    # Verify patient exists and belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == invoice_data.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Generate invoice number
    from datetime import datetime
    today = datetime.now()
    invoice_count = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.practice_id == current_user.practice_id,
            func.date(Invoice.created_at) == today.date()
        )
    )
    count = invoice_count.scalar() or 0
    
    invoice_number = f"INV-{today.strftime('%Y%m%d')}-{count + 1:04d}"
    
    # Calculate totals
    subtotal = sum(item.total for item in invoice_data.line_items)
    tax = subtotal * (invoice_data.tax_rate or Decimal('0.0'))
    total = subtotal + tax
    
    # Create invoice
    invoice = Invoice(
        practice_id=current_user.practice_id,
        patient_id=invoice_data.patient_id,
        invoice_number=invoice_number,
        status=invoice_data.status or InvoiceStatus.PENDING,
        subtotal=subtotal,
        tax=tax,
        total=total,
        line_items=[item.dict() for item in invoice_data.line_items],
        due_date=invoice_data.due_date,
        notes=invoice_data.notes,
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    
    return invoice


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    
    # Update fields
    update_data = invoice_data.dict(exclude_unset=True)
    
    # Recalculate totals if line items or tax rate changed
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
    invoice_id: str,
    current_user: User = Depends(get_current_user),
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    
    # Soft delete by cancelling
    invoice.status = InvoiceStatus.CANCELLED
    await db.commit()
    
    return {"message": "Invoice cancelled successfully"}


# Payment Endpoints

@router.get("/payments/", response_model=PaymentListResponse)
async def list_payments(
    invoice_id: Optional[str] = Query(None, description="Filter by invoice"),
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    status: Optional[PaymentStatus] = Query(None, description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List payments with optional filters
    """
    # Build query
    query = select(Payment).join(Invoice).where(Invoice.practice_id == current_user.practice_id)
    
    # Apply filters
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
    
    # Order by creation date (newest first)
    query = query.order_by(Payment.created_at.desc())
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    return PaymentListResponse(
        payments=payments,
        count=len(payments),
    )


@router.post("/payments/", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create new payment
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
    
    # Verify patient exists and belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == payment_data.patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # Create payment
    payment = Payment(
        invoice_id=payment_data.invoice_id,
        patient_id=payment_data.patient_id,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        transaction_id=payment_data.transaction_id,
        status=payment_data.status or PaymentStatus.COMPLETED,
        notes=payment_data.notes,
    )
    
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    
    # Update invoice status if fully paid
    if invoice.balance_due <= 0:
        invoice.status = InvoiceStatus.PAID
        await db.commit()
    
    return payment


@router.get("/summary", response_model=BillingSummary)
async def get_billing_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get billing summary for the practice
    """
    # Build date filter
    date_filter = []
    if start_date:
        date_filter.append(func.date(Invoice.created_at) >= start_date)
    if end_date:
        date_filter.append(func.date(Invoice.created_at) <= end_date)
    
    # Get invoice statistics
    invoice_query = select(
        func.count(Invoice.id).label('total_invoices'),
        func.sum(Invoice.total).label('total_revenue'),
        func.sum(Invoice.tax).label('total_tax'),
    ).where(
        Invoice.practice_id == current_user.practice_id,
        *date_filter
    )
    
    invoice_result = await db.execute(invoice_query)
    invoice_stats = invoice_result.first()
    
    # Get payment statistics
    payment_query = select(
        func.count(Payment.id).label('total_payments'),
        func.sum(Payment.amount).label('total_collected'),
    ).join(Invoice).where(
        Invoice.practice_id == current_user.practice_id,
        *date_filter
    )
    
    payment_result = await db.execute(payment_query)
    payment_stats = payment_result.first()
    
    # Get status breakdown
    status_query = select(
        Invoice.status,
        func.count(Invoice.id).label('count'),
        func.sum(Invoice.total).label('amount'),
    ).where(
        Invoice.practice_id == current_user.practice_id,
        *date_filter
    ).group_by(Invoice.status)
    
    status_result = await db.execute(status_query)
    status_breakdown = status_result.all()
    
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