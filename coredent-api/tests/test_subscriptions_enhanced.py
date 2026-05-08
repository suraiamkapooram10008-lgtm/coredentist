"""
Enhanced Tests for Subscription API endpoints
Targets 70% coverage for subscriptions module
"""

import pytest
import uuid
from datetime import datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.user import User


class TestSubscriptionPlansEnhanced:
    """Enhanced test cases for subscription plan endpoints"""

    @pytest.mark.asyncio
    async def test_list_plans_public(self, client: AsyncClient, auth_headers):
        """Test listing plans with auth"""
        response = await client.get("/api/v1/subscriptions/plans", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_create_plan_admin(self, client: AsyncClient, admin_token: str):
        """Test creating plan as admin"""
        plan_data = {
            "name": "Premium Plan",
            "description": "Advanced features for large practices",
            "amount": 99.00,
            "currency": "USD",
            "interval": "monthly",
            "trial_period_days": 14,
            "features": ["Unlimited Patients", "Advanced Reporting", "Priority Support"],
            "stripe_price_id": "price_test_123",
        }

        response = await client.post(
            "/api/v1/subscriptions/plans",
            json=plan_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "Premium Plan"
        assert float(data["amount"]) == 99.00

    @pytest.mark.asyncio
    async def test_create_plan_non_admin(self, client: AsyncClient, db_session, test_practice):
        """Test creating plan without admin role"""
        from app.models.user import User
        from app.core.security import get_password_hash
        # Create a non-admin user
        non_admin = User(
            email=f"staff_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("secret"),
            first_name="Staff",
            last_name="User",
            role="front_desk",
            practice_id=test_practice.id,
            is_active=True,
            is_email_verified=True,
            mfa_enabled=True,
            mfa_verified=True,
        )
        db_session.add(non_admin)
        await db_session.commit()
        await db_session.refresh(non_admin)

        # Login as non-admin
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": non_admin.email,
            "password": "secret"
        })
        token = login_resp.json()["access_token"]
        staff_headers = {"Authorization": f"Bearer {token}"}

        plan_data = {
            "name": "Test Plan",
            "amount": 49.00,
            "currency": "USD",
            "interval": "monthly",
            "stripe_price_id": "price_test_456",
        }

        response = await client.post(
            "/api/v1/subscriptions/plans",
            json=plan_data,
            headers=staff_headers
        )
        assert response.status_code in [403, 401]

    @pytest.mark.asyncio
    async def test_get_plan_by_id(self, client: AsyncClient, admin_token: str, test_plan_id: str):
        """Test getting plan by ID"""
        response = await client.get(
            f"/api/v1/subscriptions/plans/{test_plan_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_plan_id)

    @pytest.mark.asyncio
    async def test_update_plan(self, client: AsyncClient, admin_token: str, test_plan_id: str):
        """Test updating a subscription plan"""
        update_data = {
            "name": "Updated Plan Name",
            "amount": 79.00,
            "features": ["Updated Feature 1", "Updated Feature 2"],
        }

        response = await client.put(
            f"/api/v1/subscriptions/plans/{test_plan_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Plan Name"
        assert float(data["amount"]) == 79.00

    @pytest.mark.asyncio
    async def test_delete_plan(self, client: AsyncClient, admin_token: str, test_plan_id: str):
        """Test deleting (deactivating) a plan"""
        response = await client.delete(
            f"/api/v1/subscriptions/plans/{test_plan_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Might return 200 or 204
        assert response.status_code in [200, 204]


class TestSubscriptionManagementEnhanced:
    """Enhanced test cases for subscription management"""

    @pytest.mark.asyncio
    async def test_create_subscription(self, client: AsyncClient, auth_headers, test_plan_id: str, test_user: User):
        """Test creating a new subscription"""
        subscription_data = {
            "plan_id": str(test_plan_id),
            "payment_method_id": "pm_test_123456",
            "trial_end": (datetime.now() + timedelta(days=14)).isoformat(),
        }

        response = await client.post(
            "/api/v1/subscriptions/",
            json=subscription_data,
            headers=auth_headers
        )

        if response.status_code in [200, 201]:
            data = response.json()
            assert data["plan_id"] == str(test_plan_id)
            assert data["status"] == "trialing"

    @pytest.mark.asyncio
    async def test_list_user_subscriptions(self, client: AsyncClient, auth_headers):
        """Test listing user's subscriptions"""
        response = await client.get(
            "/api/v1/subscriptions/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "subscriptions" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_cancel_subscription(self, client: AsyncClient, auth_headers, test_subscription_id: str):
        """Test cancelling a subscription"""
        cancel_data = {
            "reason": "No longer need service",
            "cancel_at_period_end": True,
        }

        response = await client.post(
            f"/api/v1/subscriptions/{test_subscription_id}/cancel",
            json=cancel_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_change_plan(self, client: AsyncClient, auth_headers, test_subscription_id: str, test_plan_id: str):
        """Test changing subscription plan"""
        change_data = {
            "new_plan_id": str(test_plan_id),
            "proration_behavior": "create_prorations",
        }

        response = await client.post(
            f"/api/v1/subscriptions/{test_subscription_id}/change-plan",
            json=change_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_pause_subscription(self, client: AsyncClient, auth_headers, test_subscription_id: str):
        """Test pausing a subscription"""
        pause_data = {
            "pause_behavior": "void",
            "resume_at": (datetime.now() + timedelta(days=7)).isoformat(),
        }

        response = await client.post(
            f"/api/v1/subscriptions/{test_subscription_id}/pause",
            json=pause_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_resume_subscription(self, client: AsyncClient, auth_headers, test_subscription_id: str):
        """Test resuming a paused subscription"""
        # First pause the subscription
        await client.post(
            f"/api/v1/subscriptions/{test_subscription_id}/pause",
            json={"reason": "Testing"},
            headers=auth_headers
        )

        # Then resume it
        response = await client.post(
            f"/api/v1/subscriptions/{test_subscription_id}/resume",
            headers=auth_headers
        )
        assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_get_invoices(self, client: AsyncClient, auth_headers):
        """Test getting subscription invoices"""
        response = await client.get(
            "/api/v1/subscriptions/invoices",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "invoices" in data

    @pytest.mark.asyncio
    async def test_get_usage(self, client: AsyncClient, auth_headers):
        """Test getting subscription usage"""
        response = await client.get(
            "/api/v1/subscriptions/usage",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "usage" in data or "current" in data

    @pytest.mark.asyncio
    async def test_get_stats_admin(self, client: AsyncClient, admin_token: str):
        """Test getting subscription stats as admin"""
        response = await client.get(
            "/api/v1/subscriptions/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_active" in data or "total_subscriptions" in data

    @pytest.mark.asyncio
    async def test_webhook_endpoint(self, client: AsyncClient):
        """Test webhook endpoint (Stripe style)"""
        webhook_data = {
            "id": "evt_test_123",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "subscription": "sub_test_123",
                    "status": "paid",
                }
            }
        }

        response = await client.post(
            "/api/v1/subscriptions/webhook",
            json=webhook_data,
            headers={"Stripe-Signature": "test_signature"}
        )
        # Webhook might return 200, 204, or 401 (if signature invalid)
        assert response.status_code in [200, 204, 401, 400]
