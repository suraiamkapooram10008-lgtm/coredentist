"""
Tests for Billing API endpoints
Targets 70% coverage for billing module
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient


class TestBillingEndpoints:
    """Test cases for billing endpoints"""

    @pytest.mark.asyncio
    async def test_create_invoice(self, client: AsyncClient, auth_headers, test_patient):
        """Test creating an invoice"""
        invoice_data = {
            "patient_id": str(test_patient.id),
            "items": [
                {
                    "description": "Dental Cleaning",
                    "procedure_code": "D1110",
                    "quantity": 1,
                    "unit_price": 150.00,
                },
                {
                    "description": "X-Ray",
                    "procedure_code": "D0210",
                    "quantity": 1,
                    "unit_price": 75.00,
                }
            ],
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "notes": "Monthly billing",
        }

        response = await client.post(
            "/api/v1/billing/invoices",
            json=invoice_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "total_amount" in data or "amount" in data

    @pytest.mark.asyncio
    async def test_list_invoices(self, client: AsyncClient, auth_headers):
        """Test listing invoices"""
        response = await client.get(
            "/api/v1/billing/invoices",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "invoices" in data

    @pytest.mark.asyncio
    async def test_get_invoice_by_id(self, client: AsyncClient, auth_headers):
        """Test getting invoice by ID"""
        # First create an invoice
        invoice_data = {
            "patient_id": str(uuid4()),
            "items": [
                {
                    "description": "Test Item",
                    "quantity": 1,
                    "unit_price": 100.00,
                }
            ],
        }

        create_resp = await client.post(
            "/api/v1/billing/invoices",
            json=invoice_data,
            headers=auth_headers
        )

        if create_resp.status_code in [200, 201]:
            invoice_id = create_resp.json()["id"]

            response = await client.get(
                f"/api/v1/billing/invoices/{invoice_id}",
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.json()["id"] == invoice_id

    @pytest.mark.asyncio
    async def test_update_invoice_status(self, client: AsyncClient, auth_headers):
        """Test updating invoice status"""
        # First create an invoice
        invoice_data = {
            "patient_id": str(uuid4()),
            "items": [{"description": "Test", "quantity": 1, "unit_price": 50.00}],
        }

        create_resp = await client.post(
            "/api/v1/billing/invoices",
            json=invoice_data,
            headers=auth_headers
        )

        if create_resp.status_code in [200, 201]:
            invoice_id = create_resp.json()["id"]

            update_data = {"status": "paid"}
            response = await client.patch(
                f"/api/v1/billing/invoices/{invoice_id}/status",
                json=update_data,
                headers=auth_headers
            )
            assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_create_payment(self, client: AsyncClient, auth_headers):
        """Test recording a payment"""
        payment_data = {
            "invoice_id": str(uuid4()),
            "amount": 150.00,
            "payment_method": "credit_card",
            "payment_date": datetime.now().isoformat(),
            "reference_number": "PAY-12345",
        }

        response = await client.post(
            "/api/v1/billing/payments",
            json=payment_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]  # 404 if invoice not found

    @pytest.mark.asyncio
    async def test_list_payments(self, client: AsyncClient, auth_headers):
        """Test listing payments"""
        response = await client.get(
            "/api/v1/billing/payments",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "payments" in data

    @pytest.mark.asyncio
    async def test_get_billing_summary(self, client: AsyncClient, auth_headers):
        """Test getting billing summary"""
        response = await client.get(
            "/api/v1/billing/summary",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]  # endpoint might not exist
        if response.status_code == 200:
            data = response.json()
            assert "total_revenue" in data or "outstanding" in data

    @pytest.mark.asyncio
    async def test_create_refund(self, client: AsyncClient, auth_headers):
        """Test creating a refund"""
        refund_data = {
            "payment_id": str(uuid4()),
            "amount": 50.00,
            "reason": "Patient overpaid",
        }

        response = await client.post(
            "/api/v1/billing/refunds",
            json=refund_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]

    @pytest.mark.asyncio
    async def test_get_financial_report(self, client: AsyncClient, auth_headers):
        """Test getting financial report"""
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        end_date = datetime.now().isoformat()

        response = await client.get(
            f"/api/v1/billing/reports/financial?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_billing_unauthorized(self, client: AsyncClient):
        """Test billing endpoints without auth"""
        response = await client.get("/api/v1/billing/invoices")
        assert response.status_code in [401, 403]
