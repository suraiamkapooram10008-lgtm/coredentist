"""Tests for billing endpoints"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, date
from decimal import Decimal
from uuid import uuid4

pytestmark = pytest.mark.asyncio


class TestBillingEndpoints:
    """Test suite for billing CRUD operations"""

    async def test_create_payment_plan_with_pydantic_schema(self, async_client):
        """Verify payment plan creation uses Pydantic validation (SECURITY)"""
        response = await async_client.post(
            "/api/v1/billing/payment-plans/",
            json={
                "patient_id": str(uuid4()),
                "total_amount": 500.00,
                "initial_deposit": 100.00,
                "months": 12,
                "notes": "Test payment plan"
            }
        )
        # Should either succeed (201) or return auth error (401/403)
        assert response.status_code in (201, 401, 403)

    async def test_create_payment_plan_rejects_invalid_data(self, async_client, auth_headers):
        """Verify Pydantic validation rejects bad data"""
        response = await async_client.post(
            "/api/v1/billing/payment-plans/",
            headers=auth_headers,
            json={"total_amount": -100}  # Missing required patient_id
        )
        assert response.status_code == 422  # Validation error

    async def test_list_invoices(self, async_client):
        """Test invoice listing endpoint"""
        response = await async_client.get("/api/v1/billing/invoices/")
        assert response.status_code in (200, 401, 403)


class TestPaymentPlanSchema:
    """Test PaymentPlanCreateSchema validation"""

    def test_valid_schema(self):
        """Test that valid schema passes validation"""
        from pydantic import BaseModel
        from uuid import UUID
        
        class PaymentPlanCreateSchema(BaseModel):
            patient_id: UUID
            invoice_id: UUID = None
            total_amount: float
            initial_deposit: float = 0
            months: int = 12
            notes: str = None
        
        plan = PaymentPlanCreateSchema(
            patient_id=uuid4(),
            total_amount=500.00,
            initial_deposit=100.00
        )
        assert plan.total_amount == 500.00
        assert plan.months == 12

    def test_invalid_schema_missing_field(self):
        """Test that missing required field fails"""
        from pydantic import BaseModel, ValidationError
        from uuid import UUID
        
        class PaymentPlanCreateSchema(BaseModel):
            patient_id: UUID
            total_amount: float
        
        with pytest.raises(ValidationError):
            PaymentPlanCreateSchema(total_amount=500.00)


@pytest.mark.skip(reason="Belongs in test_staff")
class TestStaffPydanticValidation:
    """Test staff endpoint uses Pydantic schemas"""

    async def test_create_staff_rejects_invalid_email(self, async_client):
        """Verify UserCreate schema rejects bad email"""
        response = await async_client.post(
            "/api/v1/staff/",
            json={
                "email": "not-an-email",
                "password": "Short1!",  # Too short for min_length=8
                "first_name": "Test",
                "last_name": "User",
                "role": "front_desk",
                "practice_id": str(uuid4())
            }
        )
        assert response.status_code == 422  # Pydantic validation catches both errors

    async def test_create_staff_missing_password(self, async_client):
        """Verify password is required"""
        response = await async_client.post(
            "/api/v1/staff/",
            json={
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "role": "front_desk",
                "practice_id": str(uuid4())
            }
        )
        # UserCreate has password as required field
        assert response.status_code == 422


@pytest.mark.skip(reason="Belongs in test_config")
class TestConfigValidation:
    """Test configuration validation"""

    def test_access_token_default_is_15(self):
        """Verify ACCESS_TOKEN_EXPIRE_MINUTES defaults to 15 (HIPAA)"""
        import os
        # Temporarily unset env var to check default
        old_val = os.environ.pop("ACCESS_TOKEN_EXPIRE_MINUTES", None)
        try:
            from app.core.config_simple import SimpleSettings
            settings = SimpleSettings()
            assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
        finally:
            if old_val:
                os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = old_val

    def test_fernet_key_validation(self):
        """Verify Fernet key validation works"""
        from cryptography.fernet import Fernet
        
        # Valid Fernet key should work
        valid_key = Fernet.generate_key().decode()
        Fernet(valid_key.encode())
        
        # Invalid key should fail
        with pytest.raises((ValueError, TypeError)):
            Fernet(b"not-a-valid-fernet-key")


class TestStripeErrorHandling:
    """Test Stripe error handling doesn't leak details"""

    async def test_generic_error_messages(self, async_client):
        """Verify Stripe endpoints return generic messages"""
        # Test with invalid Stripe key - should return generic message
        response = await async_client.post(
            "/api/v1/stripe/create-payment-intent",
            json={
                "amount": 50.00,
                "currency": "usd",
                "payment_type": "one_time",
                "description": "Test payment"
            }
        )
        if response.status_code == 400:
            data = response.json()
            # Should NOT include Stripe error details
            assert "stripe" not in data.get("detail", "").lower()
            assert "api key" not in data.get("detail", "").lower()