"""
Tests for health check endpoints
"""
import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health monitoring endpoints"""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test main health check endpoint"""
        response = await client.get("/api/v1/health/")
        assert response.status_code in (200, 503)

    @pytest.mark.asyncio
    async def test_liveness_check(self, client: AsyncClient):
        """Test Kubernetes liveness probe"""
        response = await client.get("/api/v1/health/liveness")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_readiness_check(self, client: AsyncClient):
        """Test Kubernetes readiness probe"""
        response = await client.get("/api/v1/health/readiness")
        assert response.status_code in (200, 503)

    @pytest.mark.asyncio
    async def test_sentry_health_check(self, client: AsyncClient):
        """Test Sentry health check endpoint"""
        response = await client.get("/api/v1/health/sentry")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_check(self, client: AsyncClient):
        """Test metrics endpoint"""
        response = await client.get("/api/v1/health/metrics")
        assert response.status_code == 200
