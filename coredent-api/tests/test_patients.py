"""
Tests for patient endpoints
"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestPatientEndpoints:
    """Test patient management endpoints"""

    @pytest.mark.asyncio
    async def test_get_patients_success(self, client: AsyncClient, auth_headers):
        """Test getting patients list"""
        response = await client.get("/api/v1/patients", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_patients_unauthorized(self, client: AsyncClient):
        """Test getting patients without authentication"""
        response = await client.get("/api/v1/patients")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_patient_by_id_success(self, client: AsyncClient, auth_headers, test_patient):
        """Test getting patient by ID"""
        response = await client.get(f"/api/v1/patients/{test_patient.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert str(data["id"]) == str(test_patient.id)
        assert data["first_name"] == test_patient.first_name
        assert data["last_name"] == test_patient.last_name
        assert data["email"] == test_patient.email

    @pytest.mark.asyncio
    async def test_get_patient_by_id_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent patient"""
        nonexistent_id = str(uuid.uuid4())  # Generate a valid UUID that doesn't exist
        response = await client.get(f"/api/v1/patients/{nonexistent_id}", headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_patient_success(self, client: AsyncClient, auth_headers):
        """Test creating new patient"""
        patient_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "+1987654321",
            "date_of_birth": "1985-05-15",
            "gender": "female",
            "address": {
                "street": "456 Oak Ave",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62702",
                "country": "USA"
            },
            "emergency_contact": {
                "name": "John Smith",
                "relationship": "spouse",
                "phone": "+1987654322"
            },
            "medical_alerts": ["Allergic to penicillin"],
            "status": "active"
        }

        response = await client.post("/api/v1/patients", json=patient_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == patient_data["first_name"]
        assert data["last_name"] == patient_data["last_name"]
        assert data["email"] == patient_data["email"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_patient_validation_error(self, client: AsyncClient, auth_headers):
        """Test creating patient with invalid data"""
        patient_data = {
            "first_name": "",  # Empty name should fail validation
            "email": "invalid-email"  # Invalid email format
        }

        response = await client.post("/api/v1/patients", json=patient_data, headers=auth_headers)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_email(self, client: AsyncClient, auth_headers, test_patient):
        """Test creating patient with duplicate email"""
        patient_data = {
            "first_name": "Another",
            "last_name": "Patient",
            "email": test_patient.email,  # Duplicate email
            "phone": "+1111111111",
            "date_of_birth": "1990-01-01",
            "gender": "male"
        }

        response = await client.post("/api/v1/patients", json=patient_data, headers=auth_headers)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_patient_success(self, client: AsyncClient, auth_headers, test_patient):
        """Test updating patient"""
        update_data = {
            "phone": "+1999999999",
            "address_street": "789 Pine St",
            "address_city": "Springfield",
            "address_state": "IL",
            "address_zip": "62703"
        }

        response = await client.put(f"/api/v1/patients/{test_patient.id}",
                            json=update_data, headers=auth_headers)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_patient_not_found(self, client: AsyncClient, auth_headers):
        """Test updating non-existent patient"""
        nonexistent_id = str(uuid.uuid4())
        update_data = {"phone": "+1999999999"}

        response = await client.put(f"/api/v1/patients/{nonexistent_id}",
                            json=update_data, headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_patient_forbidden_for_dentist(self, client: AsyncClient, db_session, test_practice, test_patient):
        """Test deleting patient as dentist (should be forbidden - requires admin/owner)"""
        from app.models.user import User
        from app.core.security import get_password_hash
        # Create a dentist user
        dentist = User(
            email=f"dentist_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("secret"),
            first_name="Dentist",
            last_name="User",
            role="dentist",
            practice_id=test_practice.id,
            is_active=True,
            is_email_verified=True,
            mfa_enabled=True,
            mfa_verified=True,
        )
        db_session.add(dentist)
        await db_session.commit()
        await db_session.refresh(dentist)

        # Login as dentist
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": dentist.email,
            "password": "secret"
        })
        token = login_resp.json()["access_token"]
        dentist_headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete(f"/api/v1/patients/{test_patient.id}", headers=dentist_headers)

        # Dentist role should get 403 Forbidden
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_patient_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting non-existent patient as owner/admin"""
        nonexistent_id = str(uuid.uuid4())
        response = await client.delete(f"/api/v1/patients/{nonexistent_id}", headers=auth_headers)

        # Owner/admin gets 404 for non-existent patient
        assert response.status_code == 404
