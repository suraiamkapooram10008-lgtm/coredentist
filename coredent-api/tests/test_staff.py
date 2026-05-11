"""Tests for staff management endpoints (Pydantic validation, RBAC)"""
import pytest
from uuid import uuid4
from app.models.user import UserRole

pytestmark = pytest.mark.asyncio


class TestStaffPydanticValidation:
    """Verify staff endpoints use Pydantic schemas"""

    async def test_create_staff_rejects_invalid_email(self, async_client, auth_headers):
        response = await async_client.post(
            "/api/v1/staff/",
            headers=auth_headers,
            json={
                "email": "not-an-email",
                "password": "ValidPass123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "FRONT_DESK",
                "practice_id": str(uuid4())
            }
        )
        assert response.status_code == 422

    async def test_create_staff_validates_password_length(self, async_client, auth_headers):
        response = await async_client.post(
            "/api/v1/staff/",
            headers=auth_headers,
            json={
                "email": "user@example.com",
                "password": "Ab1",  # Only 3 chars, min is 8
                "first_name": "Test",
                "last_name": "User",
                "role": "FRONT_DESK",
                "practice_id": str(uuid4())
            }
        )
        assert response.status_code in (422, 400)

    async def test_create_staff_validates_role(self, async_client, auth_headers):
        response = await async_client.post(
            "/api/v1/staff/",
            headers=auth_headers,
            json={
                "email": "user@example.com",
                "password": "ValidPass123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "invalid_role",
                "practice_id": str(uuid4())
            }
        )
        assert response.status_code == 422


class TestStaffListing:
    """Test staff listing permissions"""

    async def test_list_staff_requires_auth(self, async_client):
        response = await async_client.get("/api/v1/staff/")
        assert response.status_code == 401


class TestStaffUpdateSchema:
    """Test staff update uses UserUpdate Pydantic schema"""

    def test_user_update_allows_partial_updates(self):
        from app.schemas.user import UserUpdate
        data = UserUpdate(first_name="NewName")
        assert data.first_name == "NewName"
        assert data.email is None
        assert data.role is None

    def test_user_update_validates_email(self):
        from pydantic import ValidationError
        from app.schemas.user import UserUpdate
        with pytest.raises(ValidationError):
            UserUpdate(email="not-an-email")

    def test_user_update_password_not_exposed(self):
        from app.schemas.user import UserUpdate
        data = UserUpdate()
        assert not hasattr(data, 'password')