"""
Tests for patient portal endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import secrets


def _hash_portal_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class TestPatientPortal:
    """Test patient portal endpoints"""

    @pytest.mark.asyncio
    async def test_get_my_profile_invalid_token(self, client: AsyncClient):
        """Test getting profile with invalid token"""
        response = await client.get(
            "/api/v1/portal/me",
            params={"token": "invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_appointments_invalid_token(self, client: AsyncClient):
        """Test getting appointments with invalid token"""
        response = await client.get(
            "/api/v1/portal/appointments",
            params={"token": "invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_billing_invalid_token(self, client: AsyncClient):
        """Test getting billing with invalid token"""
        response = await client.get(
            "/api/v1/portal/billing",
            params={"token": "invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_treatment_plans_invalid_token(self, client: AsyncClient):
        """Test getting treatment plans with invalid token"""
        response = await client.get(
            "/api/v1/portal/treatment-plans",
            params={"token": "invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_insurance_invalid_token(self, client: AsyncClient):
        """Test getting insurance with invalid token"""
        response = await client.get(
            "/api/v1/portal/insurance",
            params={"token": "invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_make_payment_invalid_token(self, client: AsyncClient):
        """Test making payment with invalid token"""
        response = await client.post(
            "/api/v1/portal/pay",
            params={"token": "invalid", "invoice_id": "test-id", "amount": 100.0},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_documents_invalid_token(self, client: AsyncClient):
        """Test getting documents with invalid token"""
        response = await client.get(
            "/api/v1/portal/documents",
            params={"token": "invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_sign_document_invalid_token(self, client: AsyncClient):
        """Test signing document with invalid token"""
        response = await client.post(
            "/api/v1/portal/documents/non-existent/sign",
            params={"token": "invalid", "signature_data": "test"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_profile_missing_token(self, client: AsyncClient):
        """Test getting profile without token parameter"""
        response = await client.get("/api/v1/portal/me")
        assert response.status_code in [422, 401]

    @pytest.mark.asyncio
    async def test_get_my_appointments_missing_token(self, client: AsyncClient):
        """Test getting appointments without token parameter"""
        response = await client.get("/api/v1/portal/appointments")
        assert response.status_code in [422, 401]

    @pytest.mark.asyncio
    async def test_get_my_billing_missing_token(self, client: AsyncClient):
        """Test getting billing without token parameter"""
        response = await client.get("/api/v1/portal/billing")
        assert response.status_code in [422, 401]

    @pytest.mark.asyncio
    async def test_portal_endpoint_structure(self, client: AsyncClient):
        """Test that portal endpoints exist (401 vs 404)"""
        endpoints = [
            "/api/v1/portal/me",
            "/api/v1/portal/appointments",
            "/api/v1/portal/billing",
            "/api/v1/portal/treatment-plans",
            "/api/v1/portal/insurance",
            "/api/v1/portal/documents",
        ]
        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code in [401, 422], f"{endpoint} returned {response.status_code}"
