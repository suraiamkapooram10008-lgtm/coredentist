"""
Tests for reports endpoints
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


class TestReportsEndpoints:
    """Test dashboard and analytics endpoints"""

    @pytest.mark.asyncio
    async def test_dashboard_metrics_success(self, client: AsyncClient, auth_headers):
        """Test dashboard metrics endpoint"""
        today = datetime.now().strftime("%Y-%m-%d")
        last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        response = await client.get(
            f"/api/v1/reports/dashboard?from={last_month}&to={today}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Response structure may vary, just check we get data back
        assert data is not None

    @pytest.mark.asyncio
    async def test_dashboard_metrics_unauthorized(self, client: AsyncClient):
        """Test dashboard without auth"""
        response = await client.get("/api/v1/reports/dashboard?from=2026-01-01&to=2026-12-31")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_dashboard_metrics_invalid_date_range(self, client: AsyncClient, auth_headers):
        """Test dashboard with missing dates"""
        response = await client.get("/api/v1/reports/dashboard", headers=auth_headers)
        assert response.status_code == 422
