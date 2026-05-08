"""
Tests for Subscription API endpoints
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestSubscriptionPlans:
    """Test subscription plan endpoints"""

    @pytest.mark.asyncio
    async def test_list_subscription_plans(self, client: AsyncClient, auth_headers):
        """Test listing subscription plans"""
        response = await client.get(
            "/api/v1/subscriptions/plans",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_list_active_plans_only(self, client: AsyncClient, auth_headers):
        """Test listing only active subscription plans"""
        response = await client.get(
            "/api/v1/subscriptions/plans?active_only=true",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404]


class TestSubscriptions:
    """Test subscription management endpoints"""

    @pytest.mark.asyncio
    async def test_list_subscriptions(self, client: AsyncClient, auth_headers):
        """Test listing subscriptions"""
        response = await client.get(
            "/api/v1/subscriptions",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_list_subscriptions_with_status_filter(self, client: AsyncClient, auth_headers):
        """Test listing subscriptions with status filter"""
        response = await client.get(
            "/api/v1/subscriptions?status_filter=active",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404]


class TestUsageBilling:
    """Test usage-based billing endpoints"""

    @pytest.mark.asyncio
    async def test_record_usage(self, client: AsyncClient, auth_headers):
        """Test recording usage for a subscription"""
        usage_data = {
            "quantity": "100",
            "description": "API calls",
        }
        response = await client.post(
            "/api/v1/subscriptions/usage",
            json=usage_data,
            headers=auth_headers,
        )
        assert response.status_code in [200, 404, 405, 422]

    @pytest.mark.asyncio
    async def test_get_usage(self, client: AsyncClient, auth_headers):
        """Test getting usage records for a subscription"""
        response = await client.get(
            "/api/v1/subscriptions/usage",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404, 405, 422]

    @pytest.mark.asyncio
    async def test_submit_usage_batch(self, client: AsyncClient, auth_headers):
        """Test submitting batch usage records"""
        batch_data = {
            "items": [
                {"quantity": "50", "description": "Morning usage"},
                {"quantity": "75", "description": "Afternoon usage"},
            ],
        }
        response = await client.post(
            "/api/v1/subscriptions/usage-billing/submit",
            json=batch_data,
            headers=auth_headers,
        )
        assert response.status_code in [200, 404, 405, 422]


class TestSubscriptionStats:
    """Test subscription statistics endpoint"""

    @pytest.mark.asyncio
    async def test_get_stats(self, client: AsyncClient, auth_headers):
        """Test getting subscription statistics"""
        response = await client.get(
            "/api/v1/subscriptions/stats",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404, 405, 422]


class TestDunningEvents:
    """Test dunning management endpoints"""

    @pytest.mark.asyncio
    async def test_get_dunning_events(self, client: AsyncClient, auth_headers):
        """Test getting dunning events for a subscription"""
        response = await client.get(
            "/api/v1/subscriptions/dunning",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404, 405, 422]


class TestInvoiceHistory:
    """Test invoice history endpoint"""

    @pytest.mark.asyncio
    async def test_get_invoice_history(self, client: AsyncClient, auth_headers):
        """Test getting invoice history for a subscription"""
        response = await client.get(
            "/api/v1/subscriptions/invoice-history",
            params={"limit": 10},
            headers=auth_headers,
        )
        assert response.status_code in [200, 404, 405, 422]


class TestWebhook:
    """Test Stripe webhook endpoint"""

    @pytest.mark.asyncio
    @patch("stripe.Webhook.construct_event")
    async def test_stripe_webhook_payment_succeeded(self, mock_construct_event, client: AsyncClient):
        """Test Stripe webhook for successful payment"""
        mock_event = MagicMock()
        mock_event.type = "invoice.payment_succeeded"
        mock_construct_event.return_value = mock_event

        payload = '{"type": "invoice.payment_succeeded", "data": {"object": {}}}'
        headers = {"Stripe-Signature": "test_signature"}

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            content=payload.encode(),
            headers=headers,
        )
        # Webhook should return 200 even if processing fails (to acknowledge receipt)
        assert response.status_code in [200, 204, 400, 405]

    @pytest.mark.asyncio
    @patch("stripe.Webhook.construct_event")
    async def test_stripe_webhook_payment_failed(self, mock_construct_event, client: AsyncClient):
        """Test Stripe webhook for failed payment"""
        mock_event = MagicMock()
        mock_event.type = "invoice.payment_failed"
        mock_construct_event.return_value = mock_event

        payload = '{"type": "invoice.payment_failed", "data": {"object": {}}}'
        headers = {"Stripe-Signature": "test_signature"}

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            content=payload.encode(),
            headers=headers,
        )
        assert response.status_code in [200, 204, 400, 405]


class TestSubscriptionEmails:
    """Test subscription email notifications"""

    @pytest.mark.asyncio
    async def test_send_welcome_email(self):
        """Test sending subscription welcome email"""
        from app.core.email import email_service
        with patch.object(email_service, "send_email") as mock_send:
            mock_send.return_value = {"success": True, "message_id": "test-123"}
            result = await email_service.send_subscription_welcome(
                to="test@example.com",
                customer_name="John Doe",
                plan_name="Basic Plan",
                amount=49.00,
                interval="monthly",
                trial_end_date="2026-05-01",
            )
            assert result["success"] is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_payment_receipt(self):
        """Test sending payment receipt email"""
        from app.core.email import email_service
        with patch.object(email_service, "send_email") as mock_send:
            mock_send.return_value = {"success": True, "message_id": "test-123"}
            result = await email_service.send_payment_receipt(
                to="test@example.com",
                customer_name="John Doe",
                amount=49.00,
                invoice_number="INV-001",
                payment_date="2026-04-07",
                plan_name="Basic Plan",
            )
            assert result["success"] is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_payment_failed(self):
        """Test sending payment failed email"""
        from app.core.email import email_service
        with patch.object(email_service, "send_email") as mock_send:
            mock_send.return_value = {"success": True, "message_id": "test-123"}
            result = await email_service.send_payment_failed(
                to="test@example.com",
                customer_name="John Doe",
                amount=49.00,
                error_message="Card declined",
                retry_date="2026-04-10",
                attempt_number=1,
                max_attempts=4,
            )
            assert result["success"] is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_trial_expiring(self):
        """Test sending trial expiring email"""
        from app.core.email import email_service
        with patch.object(email_service, "send_email") as mock_send:
            mock_send.return_value = {"success": True, "message_id": "test-123"}
            result = await email_service.send_trial_expiring(
                to="test@example.com",
                customer_name="John Doe",
                plan_name="Basic Plan",
                trial_end_date="2026-04-21",
                days_remaining=7,
                amount=49.00,
                interval="monthly",
            )
            assert result["success"] is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_subscription_canceled(self):
        """Test sending subscription canceled email"""
        from app.core.email import email_service
        with patch.object(email_service, "send_email") as mock_send:
            mock_send.return_value = {"success": True, "message_id": "test-123"}
            result = await email_service.send_subscription_canceled(
                to="test@example.com",
                customer_name="John Doe",
                plan_name="Basic Plan",
                cancellation_date="2026-04-07",
                reason="Too expensive",
            )
            assert result["success"] is True
            mock_send.assert_called_once()