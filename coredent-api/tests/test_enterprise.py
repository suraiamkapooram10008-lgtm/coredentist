"""
Tests for enterprise endpoints
"""
import pytest
from httpx import AsyncClient


class TestEnterpriseEndpoints:
    """Test enterprise/multi-practice endpoints"""

    @pytest.mark.asyncio
    async def test_group_analytics_unauthorized(self, client: AsyncClient):
        """Test getting group analytics without authentication"""
        response = await client.get("/api/v1/enterprise/group/analytics")
        assert response.status_code in [401, 403, 404]

    @pytest.mark.asyncio
    async def test_group_practices_unauthorized(self, client: AsyncClient):
        """Test listing group practices without authentication"""
        response = await client.get("/api/v1/enterprise/group/practices")
        assert response.status_code in [401, 403, 404]

    @pytest.mark.asyncio
    async def test_group_analytics_forbidden_regular_user(self, client: AsyncClient, auth_headers):
        """Test that regular users cannot access group analytics"""
        response = await client.get("/api/v1/enterprise/group/analytics", headers=auth_headers)
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_group_practices_forbidden_regular_user(self, client: AsyncClient, auth_headers):
        """Test that regular users cannot list group practices"""
        response = await client.get("/api/v1/enterprise/group/practices", headers=auth_headers)
        assert response.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_group_analytics_with_date_params(self, client: AsyncClient, auth_headers):
        """Test group analytics with date range parameters"""
        response = await client.get(
            "/api/v1/enterprise/group/analytics?start_date=2026-01-01&end_date=2026-05-01",
            headers=auth_headers,
        )
        assert response.status_code in [403, 404]
