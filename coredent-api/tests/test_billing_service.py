"""
Tests for Billing Service
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.billing_service import BillingService
from app.models.billing import Invoice, InvoiceStatus
from app.schemas.billing import InvoiceCreate, InvoiceItemCreate


class TestBillingService:
    """Test billing service business logic"""

    def test_create_invoice_success(self, db, test_practice, test_patient, test_user):
        """Test creating an invoice successfully"""
        
        items = [
            InvoiceItemCreate(
                description="Dental Cleaning",
                quantity=1,
                unit_price=Decimal("100.00"),
                procedure_code="D1110"
            ),
            InvoiceItemCreate(
                description="X-Ray",
                quantity=2,
                unit_price=Decimal("50.00"),
                procedure_code="D0210"
            )
        ]
        
        invoice_data = InvoiceCreate(
            patient_id=test_patient.id,
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items,
            notes="Regular checkup"
        )
        
        invoice = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        assert invoice.id is not None
        assert invoice.patient_id == test_patient.id
        assert invoice.subtotal == Decimal("200.00")
        assert invoice.total == Decimal("200.00")
        assert invoice.balance_due == Decimal("200.00")
        assert invoice.status == InvoiceStatus.DRAFT
        assert len(invoice.line_items) == 2

    def test_generate_invoice_number(self, db, test_practice, test_patient, test_user):
        """Test invoice number generation"""
        
        items = [
            InvoiceItemCreate(
                description="Test",
                quantity=1,
                unit_price=Decimal("100.00")
            )
        ]
        
        invoice_data = InvoiceCreate(
            patient_id=test_patient.id,
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items
        )
        
        invoice1 = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        invoice2 = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        assert invoice1.invoice_number != invoice2.invoice_number
        assert "INV-" in invoice1.invoice_number
        assert "INV-" in invoice2.invoice_number

    def test_update_invoice_status_valid_transition(self, db, test_practice, test_patient, test_user):
        """Test valid invoice status transition"""
        
        items = [
            InvoiceItemCreate(
                description="Test",
                quantity=1,
                unit_price=Decimal("100.00")
            )
        ]
        
        invoice_data = InvoiceCreate(
            patient_id=test_patient.id,
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items
        )
        
        invoice = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        # Update from DRAFT to SENT
        updated = BillingService.update_invoice_status(
            db=db,
            invoice_id=invoice.id,
            new_status=InvoiceStatus.SENT,
            practice_id=test_practice.id
        )
        
        assert updated.status == InvoiceStatus.SENT

    def test_update_invoice_status_invalid_transition(self, db, test_practice, test_patient, test_user):
        """Test invalid invoice status transition"""
        
        items = [
            InvoiceItemCreate(
                description="Test",
                quantity=1,
                unit_price=Decimal("100.00")
            )
        ]
        
        invoice_data = InvoiceCreate(
            patient_id=test_patient.id,
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items
        )
        
        invoice = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        # Try to update from DRAFT to PAID (invalid)
        with pytest.raises(ValueError, match="Invalid status transition"):
            BillingService.update_invoice_status(
                db=db,
                invoice_id=invoice.id,
                new_status=InvoiceStatus.PAID,
                practice_id=test_practice.id
            )

    def test_record_payment_success(self, db, test_practice, test_patient, test_user):
        """Test recording a payment"""
        
        items = [
            InvoiceItemCreate(
                description="Test",
                quantity=1,
                unit_price=Decimal("100.00")
            )
        ]
        
        invoice_data = InvoiceCreate(
            patient_id=test_patient.id,
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items
        )
        
        invoice = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        # Record payment
        payment = BillingService.record_payment(
            db=db,
            invoice_id=invoice.id,
            amount=Decimal("50.00"),
            payment_method="cash",
            practice_id=test_practice.id
        )
        
        assert payment.id is not None
        assert payment.amount == Decimal("50.00")

    def test_record_payment_full_amount(self, db, test_practice, test_patient, test_user):
        """Test recording full payment"""
        
        items = [
            InvoiceItemCreate(
                description="Test",
                quantity=1,
                unit_price=Decimal("100.00")
            )
        ]
        
        invoice_data = InvoiceCreate(
            patient_id=test_patient.id,
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items
        )
        
        invoice = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        # Record full payment
        payment = BillingService.record_payment(
            db=db,
            invoice_id=invoice.id,
            amount=Decimal("200.00"),
            payment_method="cash",
            practice_id=test_practice.id
        )
        
        assert payment.amount == Decimal("200.00")

    def test_record_payment_exceeds_balance(self, db, test_practice, test_patient, test_user):
        """Test recording payment that exceeds balance"""
        
        items = [
            InvoiceItemCreate(
                description="Test",
                quantity=1,
                unit_price=Decimal("100.00")
            )
        ]
        
        invoice_data = InvoiceCreate(
            patient_id=test_patient.id,
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items
        )
        
        invoice = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        # Try to record payment exceeding balance
        with pytest.raises(ValueError, match="exceeds balance due"):
            BillingService.record_payment(
                db=db,
                invoice_id=invoice.id,
                amount=Decimal("300.00"),
                payment_method="cash",
                practice_id=test_practice.id
            )

    def test_record_payment_negative_amount(self, db, test_practice, test_patient, test_user):
        """Test recording negative payment"""
        
        items = [
            InvoiceItemCreate(
                description="Test",
                quantity=1,
                unit_price=Decimal("100.00")
            )
        ]
        
        invoice_data = InvoiceCreate(
            patient_id=test_patient.id,
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items
        )
        
        invoice = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        # Try to record negative payment
        with pytest.raises(ValueError, match="must be positive"):
            BillingService.record_payment(
                db=db,
                invoice_id=invoice.id,
                amount=Decimal("-50.00"),
                payment_method="cash",
                practice_id=test_practice.id
            )

    def test_get_billing_summary(self, db, test_practice, test_patient, test_user):
        """Test getting billing summary"""
        
        # Create multiple invoices
        for i in range(3):
            items = [
                InvoiceItemCreate(
                    description=f"Service {i}",
                    quantity=1,
                    unit_price=Decimal("100.00")
                )
            ]
            
            invoice_data = InvoiceCreate(
                patient_id=test_patient.id,
                due_date=datetime.utcnow() + timedelta(days=30),
                items=items
            )
            
            invoice = BillingService.create_invoice(
                db=db,
                invoice_data=invoice_data,
                practice_id=test_practice.id,
                created_by_id=test_user.id
            )
            
            # Pay first invoice fully
            if i == 0:
                BillingService.record_payment(
                    db=db,
                    invoice_id=invoice.id,
                    amount=Decimal("100.00"),
                    payment_method="cash",
                    practice_id=test_practice.id
                )
        
        summary = BillingService.get_billing_summary(
            db=db,
            practice_id=test_practice.id
        )
        
        assert summary["total_invoices"] == 3
        assert summary["total_billed"] == 300.00
        assert summary["total_paid"] == 100.00
        assert summary["total_outstanding"] == 200.00

    def test_get_patient_balance(self, db, test_practice, test_patient, test_user):
        """Test getting patient balance"""
        
        # Create invoices for patient
        for i in range(2):
            items = [
                InvoiceItemCreate(
                    description=f"Service {i}",
                    quantity=1,
                    unit_price=Decimal("100.00")
                )
            ]
            
            invoice_data = InvoiceCreate(
                patient_id=test_patient.id,
                due_date=datetime.utcnow() + timedelta(days=30),
                items=items
            )
            
            BillingService.create_invoice(
                db=db,
                invoice_data=invoice_data,
                practice_id=test_practice.id,
                created_by_id=test_user.id
            )
        
        balance = BillingService.get_patient_balance(
            db=db,
            patient_id=test_patient.id,
            practice_id=test_practice.id
        )
        
        assert balance["patient_id"] == test_patient.id
        assert balance["total_balance"] == 200.00
        assert balance["invoice_count"] == 2

    def test_void_invoice(self, db, test_practice, test_patient, test_user):
        """Test voiding an invoice"""
        
        items = [
            InvoiceItemCreate(
                description="Test",
                quantity=1,
                unit_price=Decimal("100.00")
            )
        ]
        
        invoice_data = InvoiceCreate(
            patient_id=test_patient.id,
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items
        )
        
        invoice = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        voided = BillingService.void_invoice(
            db=db,
            invoice_id=invoice.id,
            practice_id=test_practice.id,
            reason="Duplicate invoice"
        )
        
        assert voided.status == InvoiceStatus.VOIDED
        assert "Duplicate invoice" in voided.notes

    def test_void_invoice_with_payments(self, db, test_practice, test_patient, test_user):
        """Test voiding invoice with payments should fail"""
        
        items = [
            InvoiceItemCreate(
                description="Test",
                quantity=1,
                unit_price=Decimal("100.00")
            )
        ]
        
        invoice_data = InvoiceCreate(
            patient_id=test_patient.id,
            due_date=datetime.utcnow() + timedelta(days=30),
            items=items
        )
        
        invoice = BillingService.create_invoice(
            db=db,
            invoice_data=invoice_data,
            practice_id=test_practice.id,
            created_by_id=test_user.id
        )
        
        # Record payment
        BillingService.record_payment(
            db=db,
            invoice_id=invoice.id,
            amount=Decimal("50.00"),
            payment_method="cash",
            practice_id=test_practice.id
        )
        
        # Try to void
        with pytest.raises(ValueError, match="Cannot void invoice with payments"):
            BillingService.void_invoice(
                db=db,
                invoice_id=invoice.id,
                practice_id=test_practice.id
            )