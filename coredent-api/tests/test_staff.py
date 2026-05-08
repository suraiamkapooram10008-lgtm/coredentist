"""
Tests for staff management endpoints
"""
import pytest
import uuid
from datetime import timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestStaffEndpoints:
    """Test staff management endpoints"""

    @pytest.mark.asyncio
    async def test_list_staff_success(self, client: AsyncClient, auth_headers):
        """Test listing staff members"""
        response = await client.get("/api/v1/staff/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_staff_unauthorized(self, client: AsyncClient):
        """Test listing staff without auth"""
        response = await client.get("/api/v1/staff/")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_staff_success(self, client: AsyncClient, auth_headers):
        """Test creating a staff member"""
        staff_data = {
            "email": f"staff_{uuid.uuid4().hex[:8]}@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "role": "front_desk",
            "password": "SecurePass123!"
        }
        response = await client.post("/api/v1/staff/", json=staff_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == staff_data["email"]
        assert data["first_name"] == staff_data["first_name"]

    @pytest.mark.asyncio
    async def test_create_staff_duplicate_email(self, client: AsyncClient, auth_headers, test_user):
        """Test creating staff with duplicate email"""
        staff_data = {
            "email": test_user.email,
            "first_name": "Duplicate",
            "last_name": "User",
            "role": "front_desk",
            "password": "SecurePass123!"
        }
        response = await client.post("/api/v1/staff/", json=staff_data, headers=auth_headers)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_staff_success(self, client: AsyncClient, auth_headers, test_user):
        """Test updating a staff member"""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        response = await client.put(f"/api/v1/staff/{test_user.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_staff_not_found(self, client: AsyncClient, auth_headers):
        """Test updating non-existent staff"""
        update_data = {"first_name": "Ghost"}
        response = await client.put(f"/api/v1/staff/{uuid.uuid4()}", json=update_data, headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_inactivate_staff_success(self, client: AsyncClient, auth_headers, db_session: AsyncSession, test_practice):
        """Test inactivating a staff member"""
        from app.models.user import User
        from app.core.security import get_password_hash
        staff = User(
            email=f"inactive_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("secret"),
            first_name="Temp",
            last_name="Staff",
            role="front_desk",
            practice_id=test_practice.id,
            is_active=True,
        )
        db_session.add(staff)
        await db_session.commit()
        await db_session.refresh(staff)

        response = await client.delete(f"/api/v1/staff/{staff.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "inactivated" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_inactivate_self_fails(self, client: AsyncClient, auth_headers, test_user):
        """Test that staff cannot inactivate themselves"""
        response = await client.delete(f"/api/v1/staff/{test_user.id}", headers=auth_headers)
        assert response.status_code == 400
