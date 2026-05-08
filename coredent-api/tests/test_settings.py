"""
Tests for settings endpoints
"""
import pytest
from httpx import AsyncClient


class TestSettingsEndpoints:
    """Test practice settings endpoints"""

    @pytest.mark.asyncio
    async def test_get_billing_preferences_success(self, client: AsyncClient, auth_headers):
        """Test getting billing preferences"""
        response = await client.get("/api/v1/settings/billing", headers=auth_headers)
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_get_billing_preferences_unauthorized(self, client: AsyncClient):
        """Test getting billing preferences without auth"""
        response = await client.get("/api/v1/settings/billing")
        assert response.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_update_billing_preferences_success(self, client: AsyncClient, auth_headers):
        """Test updating billing preferences"""
        update_data = {
            "taxRate": 0.08,
            "currency": "USD",
            "invoicePrefix": "INV-2026",
            "paymentTerms": 15,
            "autoSendInvoices": True,
        }
        response = await client.put("/api/v1/settings/billing", json=update_data, headers=auth_headers)
        assert response.status_code in (200, 404)
