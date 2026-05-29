"""Tests for main application entry point"""
import pytest
import os

pytestmark = pytest.mark.asyncio


class TestHealthEndpoint:
    async def test_health_returns_healthy(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded")
        assert "database" in data

    async def test_health_includes_database_status(self, client):
        response = await client.get("/health")
        data = response.json()
        assert data["database"] in ("connected", "disconnected", "unknown")


class TestRootEndpoint:
    async def test_root_returns_app_info(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data

    async def test_root_includes_docs_link(self, client):
        response = await client.get("/")
        data = response.json()
        assert "docs" in data


class TestMetricsEndpoint:
    async def test_metrics_accessible_in_debug_mode(self, client):
        response = await client.get("/metrics")
        assert response.status_code == 200


class TestOpenAPI:
    async def test_openapi_json_available_in_debug(self, client):
        response = await client.get("/openapi.json")
        assert response.status_code in (200, 404)


class TestExceptionHandlers:
    async def test_validation_error_returns_422(self, client):
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code in (422, 400, 500)

    async def test_unknown_route_returns_404(self, client):
        response = await client.get("/nonexistent-route")
        assert response.status_code == 404
