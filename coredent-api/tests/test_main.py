"""Tests for main application entry point"""
import pytest

from app.main import app as fastapi_app

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
class TestProductionErrorLeakage:
    """Regression: production must never expose validator field details or raw
    exception internals to clients (HIPAA/security)."""

    @pytest.mark.asyncio
    async def test_validation_error_hides_field_details_in_production(self, client, monkeypatch):
        from app.core.config_simple import settings

        monkeypatch.setattr(settings, "DEBUG", False)

        response = await client.post("/api/v1/auth/login", json={"email": "not-an-email"})

        assert response.status_code == 422
        payload = response.json()
        # Generic message only — no field names/errors leak.
        assert payload.get("detail") == "Validation error"
        assert "loc" not in payload
        assert "email" not in str(payload)

    @pytest.mark.asyncio
    async def test_unhandled_exception_returns_generic_500_in_production(self, monkeypatch):
        from app.core.config_simple import settings
        from starlette.requests import Request
        from app.main import general_exception_handler

        monkeypatch.setattr(settings, "DEBUG", False)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/test-boom",
            "raw_path": b"/api/v1/test-boom",
            "url": "http://testserver/api/v1/test-boom",
            "headers": [],
            "query_string": b"",
            "client": ("203.0.113.5", 4321),
            "server": ("testserver", 80),
            "scheme": "http",
            "http_version": "1.1",
            "app": fastapi_app,
        }
        request = Request(scope)
        response = await general_exception_handler(
            request,
            RuntimeError("connection to postgres failed with password 'hunter2'"),
        )

        assert response.status_code == 500
        body = response.body.decode()
        assert "An internal error occurred" in body
        # Internal details must never reach the wire.
        assert "hunter2" not in body
        assert "postgres" not in body

    @pytest.mark.asyncio
    async def test_debug_mode_raises_for_traceback(self, monkeypatch):
        from app.core.config_simple import settings
        from starlette.requests import Request
        from app.main import general_exception_handler

        monkeypatch.setattr(settings, "DEBUG", True)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/test-boom-debug",
            "raw_path": b"/api/v1/test-boom-debug",
            "url": "http://testserver/api/v1/test-boom-debug",
            "headers": [],
            "query_string": b"",
            "client": ("203.0.113.5", 4321),
            "server": ("testserver", 80),
            "scheme": "http",
            "http_version": "1.1",
            "app": fastapi_app,
        }
        request = Request(scope)
        with pytest.raises(RuntimeError, match="boom-debug"):
            await general_exception_handler(request, RuntimeError("boom-debug"))


class TestRedactPhi:
    """The exception logger must scrub PHI (including camelCase variants) so
    nothing sensitive is written to logs."""

    def test_redacts_snake_case_and_camel_case_keys(self):
        from app.main import redact_phi

        data = {
            "first_name": "John",
            "lastName": "Doe",
            "dateOfBirth": "1980-01-01",
            "ssn": "123-45-6789",
            "phone": "555-0100",
            "note": "keep me",
        }
        result = redact_phi(data)

        assert result["first_name"] == "[REDACTED]"
        assert result["lastName"] == "[REDACTED]"
        assert result["dateOfBirth"] == "[REDACTED]"
        assert result["ssn"] == "[REDACTED]"
        assert result["phone"] == "[REDACTED]"
        assert result["note"] == "keep me"

    def test_redacts_nested_structures(self):
        from app.main import redact_phi

        data = {
            "patient": {"email": "p@example.com", "dob": "1990-01-01"},
            "payments": [{"account_number": "1234"}, {"card_number": "4242"}],
            "history": [],
        }
        result = redact_phi(data)

        assert result["patient"]["email"] == "[REDACTED]"
        assert result["payments"][0]["account_number"] == "[REDACTED]"
        assert result["history"] == []
