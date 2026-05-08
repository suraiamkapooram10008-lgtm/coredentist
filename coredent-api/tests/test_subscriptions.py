"""
Tests for Subscription API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestSubscriptionPlans:
    """Test subscription plan endpoints"""

    def test_create_subscription_plan(self, client: TestClient, admin_token: str):
        """Test creating a subscription plan"""
        plan_data = {
            "name": "Basic Plan",
            "description": "Essential features for small practices",
            "amount": 49.00,
            "currency": "USD",
            "interval": "monthly",
            "trial_period_days": 14,
            "features": ["Patient Management", "Appointment Scheduling"],
            "is_active": True,
        }
        response = client.post(
            "/api/v1/subscriptions/plans",
            json=plan_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Basic Plan"
        assert data["amount"] == 49.00
        assert data["interval"] == "monthly"
        assert data["trial_period_days"] == 14

    def test_list_subscription_plans(self, client: TestClient, admin_token: str):
        """Test listing subscription plans"""
        response = client.get(
            "/api/v1/subscriptions/plans",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_active_plans_only(self, client: TestClient, admin_token: str):
        """Test listing only active subscription plans"""
        response = client.get(
            "/api/v1/subscriptions/plans?active_only=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        for plan in data:
            assert plan["is_active"] is True

    def test_get_plan_by_id(self, client: TestClient, admin_token: str, test_plan_id: str):
        """Test getting a specific subscription plan"""
        response = client.get(
            f"/api/v1/subscriptions/plans/{test_plan_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_plan_id

    def test_update_subscription_plan(self, client: TestClient, admin_token: str, test_plan_id: str):
        """Test updating a subscription plan"""
        update_data = {
            "name": "Updated Plan",
            "amount": 59.00,
        }
        response = client.put(
            f"/api/v1/subscriptions/plans/{test_plan_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Plan"
        assert data["amount"] == 59.00

    def test_deactivate_subscription_plan(self, client: TestClient, admin_token: str, test_plan_id: str):
        """Test deactivating a subscription plan"""
        response = client.delete(
            f"/api/v1/subscriptions/plans/{test_plan_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200


class TestSubscriptions:
    """Test subscription management endpoints"""

    def test_create_subscription(self, client: TestClient, admin_token: str, test_plan_id: str):
        """Test creating a new subscription"""
        sub_data = {
            "plan_id": test_plan_id,
            "trial_period_days": 14,
        }
        response = client.post(
            "/api/v1/subscriptions",
            json=sub_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["plan_id"] == test_plan_id
        assert data["status"] in ["trialing", "active", "incomplete"]

    def test_list_subscriptions(self, client: TestClient, admin_token: str):
        """Test listing subscriptions"""
        response = client.get(
            "/api/v1/subscriptions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_subscriptions_with_status_filter(self, client: TestClient, admin_token: str):
        """Test listing subscriptions with status filter"""
        response = client.get(
            "/api/v1/subscriptions?status_filter=active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_get_subscription_by_id(self, client: TestClient, admin_token: str, test_subscription_id: str):
        """Test getting a specific subscription"""
        response = client.get(
            f"/api/v1/subscriptions/{test_subscription_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_subscription_id

    def test_cancel_subscription(self, client: TestClient, admin_token: str, test_subscription_id: str):
        """Test canceling a subscription"""
        cancel_data = {
            "cancel_at_period_end": True,
            "reason": "Testing cancellation",
        }
        response = client.post(
            f"/api/v1/subscriptions/{test_subscription_id}/cancel",
            json=cancel_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cancel_at_period_end"] is True

    def test_pause_subscription(self, client: TestClient, admin_token: str, test_subscription_id: str):
        """Test pausing a subscription"""
        pause_data = {
            "paused_until": (datetime.now() + timedelta(days=30)).isoformat(),
            "reason": "Vacation",
        }
        response = client.post(
            f"/api/v1/subscriptions/{test_subscription_id}/pause",
            json=pause_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_resume_subscription(self, client: TestClient, admin_token: str, test_subscription_id: str):
        """Test resuming a paused subscription"""
        response = client.post(
            f"/api/v1/subscriptions/{test_subscription_id}/resume",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_change_plan(self, client: TestClient, admin_token: str, test_subscription_id: str, test_plan_id: str):
        """Test changing subscription plan"""
        change_data = {
            "new_plan_id": test_plan_id,
            "proration_behavior": "create_prorations",
        }
        response = client.post(
            f"/api/v1/subscriptions/{test_subscription_id}/change-plan",
            json=change_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_preview_proration(self, client: TestClient, admin_token: str, test_subscription_id: str, test_plan_id: str):
        """Test previewing proration for plan change"""
        response = client.get(
            f"/api/v1/subscriptions/{test_subscription_id}/proration-preview",
            params={"new_plan_id": test_plan_id},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "proration_amount" in data
        assert "days_remaining" in data

    def test_get_trial_info(self, client: TestClient, admin_token: str, test_subscription_id: str):
        """Test getting trial information"""
        response = client.get(
            f"/api/v1/subscriptions/{test_subscription_id}/trial",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200


class TestUsageBilling:
    """Test usage-based billing endpoints"""

    def test_record_usage(self, client: TestClient, admin_token: str, test_subscription_id: str):
        """Test recording usage for a subscription"""
        usage_data = {
            "quantity": "100",
            "description": "API calls",
        }
        response = client.post(
            f"/api/v1/subscriptions/{test_subscription_id}/usage",
            json=usage_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 201]

    def test_get_usage(self, client: TestClient, admin_token: str, test_subscription_id: str):
        """Test getting usage records for a subscription"""
        response = client.get(
            f"/api/v1/subscriptions/{test_subscription_id}/usage",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "summaries" in data

    def test_submit_usage_batch(self, client: TestClient, admin_token: str, test_subscription_id: str):
        """Test submitting batch usage records"""
        batch_data = {
            "subscription_id": test_subscription_id,
            "items": [
                {"quantity": "50", "description": "Morning usage"},
                {"quantity": "75", "description": "Afternoon usage"},
            ],
        }
        response = client.post(
            "/api/v1/subscriptions/usage-billing/submit",
            json=batch_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 201]


class TestSubscriptionStats:
    """Test subscription statistics endpoint"""

    def test_get_stats(self, client: TestClient, admin_token: str):
        """Test getting subscription statistics"""
        response = client.get(
            "/api/v1/subscriptions/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_active" in data
        assert "mrr" in data
        assert "churn_rate" in data


class TestDunningEvents:
    """Test dunning management endpoints"""

    def test_get_dunning_events(self, client: TestClient, admin_token: str, test_subscription_id: str):
        """Test getting dunning events for a subscription"""
        response = client.get(
            f"/api/v1/subscriptions/{test_subscription_id}/dunning",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestInvoiceHistory:
    """Test invoice history endpoint"""

    def test_get_invoice_history(self, client: TestClient, admin_token: str, test_subscription_id: str):
        """Test getting invoice history for a subscription"""
        response = client.get(
            f"/api/v1/subscriptions/{test_subscription_id}/invoice-history",
            params={"limit": 10},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data


class TestWebhook:
    """Test Stripe webhook endpoint"""

    @patch("stripe.Webhook.construct_event")
    def test_stripe_webhook_payment_succeeded(self, mock_construct_event, client: TestClient):
        """Test Stripe webhook for successful payment"""
        mock_event = MagicMock()
        mock_event.type = "invoice.payment_succeeded"
        mock_construct_event.return_value = mock_event

        payload = '{"type": "invoice.payment_succeeded", "data": {"object": {}}}'
        headers = {"Stripe-Signature": "test_signature"}

        response = client.post(
            "/api/v1/subscriptions/webhook",
            content=payload.encode(),
            headers=headers,
        )
        # Webhook should return 200 even if processing fails (to acknowledge receipt)
        assert response.status_code in [200, 204, 400]

    @patch("stripe.Webhook.construct_event")
    def test_stripe_webhook_payment_failed(self, mock_construct_event, client: TestClient):
        """Test Stripe webhook for failed payment"""
        mock_event = MagicMock()
        mock_event.type = "invoice.payment_failed"
        mock_construct_event.return_value = mock_event

        payload = '{"type": "invoice.payment_failed", "data": {"object": {}}}'
        headers = {"Stripe-Signature": "test_signature"}

        response = client.post(
            "/api/v1/subscriptions/webhook",
            content=payload.encode(),
            headers=headers,
        )
        assert response.status_code in [200, 204, 400]


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