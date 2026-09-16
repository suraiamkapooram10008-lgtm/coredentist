"""Observability: Sentry initialization and Prometheus instrumentation.

Covers the gaps this change closes:

- Sentry is initialized for worker/beat, not only web. It used to live in
  app/main.py, which those processes never import, so capture_exception() inside
  a Celery task was a silent no-op.
- /metrics exposes real application metrics rather than only the default
  process/GC collectors.
- /ready separates "process is up" from "able to serve traffic".
"""
from types import SimpleNamespace

import pytest

from app.core.observability import (
    filter_sensitive_data,
    init_sentry,
    route_label,
)


class TestSentryInitialization:
    def test_missing_dsn_disables_sentry_without_failing(self, monkeypatch):
        """A deployment with no Sentry DSN must still start cleanly."""
        from app.core import observability
        from app.core.config_simple import settings

        monkeypatch.setattr(settings, "SENTRY_DSN", "")
        monkeypatch.setattr(observability, "_sentry_initialized", False)
        monkeypatch.setattr(observability, "_sentry_sdk", None)

        assert init_sentry("web") is False

    def test_init_is_idempotent(self, monkeypatch):
        """app.main and app.core.celery_app both call this; the second is a no-op."""
        from app.core import observability

        monkeypatch.setattr(observability, "_sentry_initialized", True)
        assert init_sentry("worker") is True

    def test_filter_sensitive_data_redacts_phi_and_credentials(self):
        event = {
            "request": {
                "headers": {"Authorization": "Bearer abc123", "X-Custom": "ok"},
                "data": {"email": "patient@example.com"},
            },
            "extra": {"first_name": "Ada", "date_of_birth": "1970-01-01", "note": "kept"},
        }

        filtered = filter_sensitive_data(event)

        assert filtered["request"]["headers"]["Authorization"] == "[REDACTED]"
        assert filtered["request"]["headers"]["X-Custom"] == "ok"
        assert filtered["request"]["data"]["email"] == "[REDACTED]"
        assert filtered["extra"]["first_name"] == "[REDACTED]"
        assert filtered["extra"]["date_of_birth"] == "[REDACTED]"
        # Non-sensitive context survives, otherwise the event is useless.
        assert filtered["extra"]["note"] == "kept"


class TestRouteLabel:
    """Cardinality control: raw paths would mint a series per scanner request."""

    def test_prefers_matched_route_template(self):
        request = SimpleNamespace(
            scope={"route": SimpleNamespace(path="/api/v1/patients/{patient_id}")}
        )
        assert route_label(request) == "/api/v1/patients/{patient_id}"

    def test_buckets_unmatched_requests(self):
        assert route_label(SimpleNamespace(scope={})) == "unmatched"
        assert route_label(SimpleNamespace(scope={"route": None})) == "unmatched"


class TestReadyEndpoint:
    async def test_ready_reports_each_dependency(self, async_client):
        resp = await async_client.get("/ready")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ready"
        assert body["database"] == "connected"
        # Tests run without REDIS_URL, where the limiter uses process-local
        # memory, so readiness must not demand Redis.
        assert body["redis"] == "not_configured"

    async def test_ready_returns_503_when_database_is_down(
        self, async_client, monkeypatch
    ):
        import app.main as main_module

        class _BrokenConnection:
            async def __aenter__(self):
                raise RuntimeError("database unavailable")

            async def __aexit__(self, *_exc):
                return False

        class _BrokenEngine:
            def connect(self):
                return _BrokenConnection()

        # AsyncEngine.connect is read-only, so swap the engine the endpoint uses.
        monkeypatch.setattr(main_module, "engine", _BrokenEngine())

        resp = await async_client.get("/ready")

        assert resp.status_code == 503
        assert resp.json()["status"] == "not_ready"
        assert resp.json()["database"] == "disconnected"


class TestMetricsEndpoint:
    async def test_metrics_exposes_application_metrics(self, async_client):
        await async_client.get("/health")

        resp = await async_client.get("/metrics")

        assert resp.status_code == 200
        body = resp.text
        assert "coredent_http_requests_total" in body
        assert "coredent_http_request_duration_seconds" in body
        assert "coredent_security_events_total" in body

    async def test_recorded_requests_carry_a_bounded_route_label(self, async_client):
        await async_client.get("/health")

        body = (await async_client.get("/metrics")).text

        # The route template, not the raw path.
        assert 'route="/health"' in body
        # A 404 must not create a series for the path that was guessed.
        await async_client.get("/definitely-not-a-route-xyz")
        body = (await async_client.get("/metrics")).text
        assert 'route="unmatched"' in body

    async def test_auth_failure_is_counted(self, async_client):
        unauthorized = await async_client.get("/api/v1/auth/me")
        assert unauthorized.status_code == 401

        body = (await async_client.get("/metrics")).text

        assert 'coredent_security_events_total{event_type="auth_failure"}' in body
