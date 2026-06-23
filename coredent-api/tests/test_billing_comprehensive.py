"""
Comprehensive billing endpoint tests covering invoice CRUD,
payment creation, and billing summary.
"""
import datetime
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus, PaymentMethod

pytestmark = pytest.mark.asyncio


class TestInvoiceCRUD:
    """Authenticated invoice lifecycle tests."""

    async def test_create_invoice(self, client: AsyncClient, auth_headers, test_patient):
        """Create an invoice for a patient."""
        response = await client.post(
            "/api/v1/billing/invoices/",
            headers=auth_headers,
            json={
                "patient_id": str(test_patient.id),
                "line_items": [
                    {
                        "description": "Cleaning",
                        "quantity": 1,
                        "unit_price": "100.00",
                        "total": "100.00",
                    }
                ],
                "tax_rate": "0.0",
                "notes": "Test invoice",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == str(test_patient.id)
        assert data["total"] == "100.00"
        assert data["status"] == "pending"
        assert "id" in data
        assert "invoice_number" in data

    async def test_list_invoices(self, client: AsyncClient, auth_headers, db_session, test_patient):
        """List invoices should include practice invoices."""
        inv = Invoice(
            practice_id=test_patient.practice_id,
            patient_id=test_patient.id,
            invoice_number="INV-LIST-001",
            status=InvoiceStatus.PENDING,
            subtotal=Decimal("150.00"),
            tax=Decimal("0.00"),
            total=Decimal("150.00"),
            line_items=[{"description": "Filling", "quantity": 1, "unit_price": "150.00", "total": "150.00"}],
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.get("/api/v1/billing/invoices/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(i["invoice_number"] == "INV-LIST-001" for i in data["invoices"])

    async def test_get_invoice_by_id(self, client: AsyncClient, auth_headers, db_session, test_patient):
        """Retrieve a single invoice by ID."""
        inv = Invoice(
            practice_id=test_patient.practice_id,
            patient_id=test_patient.id,
            invoice_number="INV-GET-001",
            status=InvoiceStatus.PENDING,
            subtotal=Decimal("200.00"),
            tax=Decimal("0.00"),
            total=Decimal("200.00"),
            line_items=[{"description": "Crown", "quantity": 1, "unit_price": "200.00", "total": "200.00"}],
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/billing/invoices/{inv.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(inv.id)
        assert data["invoice_number"] == "INV-GET-001"

    async def test_update_invoice(self, client: AsyncClient, auth_headers, db_session, test_patient):
        """Update invoice status."""
        inv = Invoice(
            practice_id=test_patient.practice_id,
            patient_id=test_patient.id,
            invoice_number="INV-UPD-001",
            status=InvoiceStatus.PENDING,
            subtotal=Decimal("50.00"),
            tax=Decimal("0.00"),
            total=Decimal("50.00"),
            line_items=[{"description": "Consultation", "quantity": 1, "unit_price": "50.00", "total": "50.00"}],
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.put(
            f"/api/v1/billing/invoices/{inv.id}",
            headers=auth_headers,
            json={"status": "paid"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paid"


class TestPaymentCRUD:
    """Authenticated payment lifecycle tests."""

    async def test_create_payment(self, client: AsyncClient, auth_headers, db_session, test_patient):
        """Create a payment against an invoice."""
        inv = Invoice(
            practice_id=test_patient.practice_id,
            patient_id=test_patient.id,
            invoice_number="INV-PAY-001",
            status=InvoiceStatus.PENDING,
            subtotal=Decimal("120.00"),
            tax=Decimal("0.00"),
            total=Decimal("120.00"),
            line_items=[{"description": "Service", "quantity": 1, "unit_price": "120.00", "total": "120.00"}],
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.post(
            "/api/v1/billing/payments/",
            headers=auth_headers,
            json={
                "invoice_id": str(inv.id),
                "patient_id": str(test_patient.id),
                "amount": "120.00",
                "payment_method": "cash",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "120.00"
        assert data["status"] == "completed"

    async def test_list_payments(self, client: AsyncClient, auth_headers, db_session, test_patient):
        """List payments should return practice-scoped payments."""
        inv = Invoice(
            practice_id=test_patient.practice_id,
            patient_id=test_patient.id,
            invoice_number="INV-PAY-LIST-001",
            status=InvoiceStatus.PAID,
            subtotal=Decimal("80.00"),
            tax=Decimal("0.00"),
            total=Decimal("80.00"),
            line_items=[{"description": "X-Ray", "quantity": 1, "unit_price": "80.00", "total": "80.00"}],
        )
        db_session.add(inv)
        await db_session.flush()

        pay = Payment(
            invoice_id=inv.id,
            patient_id=test_patient.id,
            amount=Decimal("80.00"),
            payment_method=PaymentMethod.CARD,
            status=PaymentStatus.COMPLETED,
        )
        db_session.add(pay)
        await db_session.commit()

        response = await client.get("/api/v1/billing/payments/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(p["id"] == str(pay.id) for p in data["payments"])


class TestBillingSummary:
    """Billing summary endpoint tests."""

    async def test_get_billing_summary(self, client: AsyncClient, auth_headers, db_session, test_patient):
        """Billing summary should reflect practice invoices and payments."""
        inv = Invoice(
            practice_id=test_patient.practice_id,
            patient_id=test_patient.id,
            invoice_number="INV-SUM-001",
            status=InvoiceStatus.PAID,
            subtotal=Decimal("300.00"),
            tax=Decimal("0.00"),
            total=Decimal("300.00"),
            line_items=[{"description": "Root canal", "quantity": 1, "unit_price": "300.00", "total": "300.00"}],
        )
        db_session.add(inv)
        await db_session.commit()

        response = await client.get("/api/v1/billing/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_invoices" in data
        assert "total_revenue" in data
        assert "outstanding_balance" in data
        assert isinstance(data["status_breakdown"], list)

    async def test_billing_summary_date_filter(self, client: AsyncClient, auth_headers):
        """Billing summary should accept date range filters without error."""
        today = datetime.date.today().isoformat()
        response = await client.get(
            f"/api/v1/billing/summary?start_date={today}&end_date={today}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_invoices" in data
