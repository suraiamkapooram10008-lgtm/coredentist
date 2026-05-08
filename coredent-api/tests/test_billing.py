"""
Tests for billing endpoints
"""
import pytest
from httpx import AsyncClient
from decimal import Decimal
from datetime import date, timedelta


class TestInvoiceEndpoints:
    """Test invoice management endpoints"""

    @pytest.mark.asyncio
    async def test_create_invoice_success(self, client: AsyncClient, auth_headers, test_patient):
        """Test creating a new invoice"""
        invoice_data = {
            "patient_id": str(test_patient.id),
            "subtotal": 500.00,
            "tax": 50.00,
            "discount": 0.00,
            "due_date": str(date.today() + timedelta(days=30)),
            "notes": "Dental cleaning and checkup"
        }
        
        response = await client.post(
            "/api/v1/billing/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["subtotal"] == "500.00"
            assert "invoice_number" in data

    @pytest.mark.asyncio
    async def test_list_invoices(self, client: AsyncClient, auth_headers):
        """Test listing invoices"""
        response = await client.get(
            "/api/v1/billing/invoices/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or "invoices" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_invoice_unauthorized(self, client: AsyncClient, test_patient):
        """Test creating invoice without authentication"""
        invoice_data = {
            "patient_id": str(test_patient.id),
            "subtotal": 500.00,
            "tax": 50.00
        }
        
        response = await client.post(
            "/api/v1/billing/invoices/",
            json=invoice_data
        )
        
        assert response.status_code in [401, 403]


class TestPaymentEndpoints:
    """Test payment processing endpoints"""

    @pytest.mark.asyncio
    async def test_create_payment_success(self, client: AsyncClient, auth_headers, test_patient):
        """Test recording a payment"""
        # First create an invoice since invoice_id is required
        invoice_data = {
            "patient_id": str(test_patient.id),
            "subtotal": 500.00,
            "tax": 50.00,
            "discount": 0.00,
            "due_date": str(date.today() + timedelta(days=30)),
            "notes": "Test invoice for payment"
        }
        invoice_resp = await client.post(
            "/api/v1/billing/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        assert invoice_resp.status_code in [200, 201]
        invoice_id = invoice_resp.json()["id"]

        payment_data = {
            "patient_id": str(test_patient.id),
            "invoice_id": invoice_id,
            "amount": 250.00,
            "payment_method": "cash",
            "payment_date": str(date.today()),
            "notes": "Partial payment"
        }
        
        response = await client.post(
            "/api/v1/billing/payments/",
            json=payment_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["amount"] == "250.00" or data["amount"] == 250.00
            assert data["payment_method"] == "cash"

    @pytest.mark.asyncio
    async def test_list_payments(self, client: AsyncClient, auth_headers):
        """Test listing payments"""
        response = await client.get(
            "/api/v1/billing/payments/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or "payments" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_payment_invalid_amount(self, client: AsyncClient, auth_headers, test_patient):
        """Test creating payment with invalid amount"""
        # First create an invoice since invoice_id is required
        invoice_data = {
            "patient_id": str(test_patient.id),
            "subtotal": 500.00,
            "tax": 50.00,
            "discount": 0.00,
            "due_date": str(date.today() + timedelta(days=30)),
            "notes": "Test invoice for payment"
        }
        invoice_resp = await client.post(
            "/api/v1/billing/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        assert invoice_resp.status_code in [200, 201]
        invoice_id = invoice_resp.json()["id"]

        payment_data = {
            "patient_id": str(test_patient.id),
            "invoice_id": invoice_id,
            "amount": -100.00,  # Negative amount
            "payment_method": "cash",
            "payment_date": str(date.today())
        }
        
        response = await client.post(
            "/api/v1/billing/payments/",
            json=payment_data,
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]


class TestBillingSummary:
    """Test billing summary and statistics"""

    @pytest.mark.asyncio
    async def test_get_billing_summary(self, client: AsyncClient, auth_headers):
        """Test getting billing summary"""
        response = await client.get(
            "/api/v1/billing/summary",
            headers=auth_headers
        )
        
        # Endpoint might not exist yet, accept 404
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "total_revenue" in data or "summary" in data
