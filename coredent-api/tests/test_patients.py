"""
Tests for patient endpoints

These tests exercise the real API contract as implemented in
app/api/v1/endpoints/patients.py:
  - Paginated list shape: {items, total, page, limit, pages}
  - Search parameter: ?query=...
  - DELETE returns 204 No Content
  - Duplicate email/phone returns 409 Conflict
"""
import datetime
import uuid as uuid_lib

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestPatientEndpoints:
    """Test patient management endpoints"""

    @pytest.mark.asyncio
    async def test_get_patients_success(
        self, client: AsyncClient, auth_headers, test_patient
    ):
        """Test getting patients list returns paginated envelope"""
        response = await client.get("/api/v1/patients", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # PaginatedResponse envelope
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data
        assert len(data["items"]) >= 1

        # Check patient data structure
        patient = data["items"][0]
        assert "id" in patient
        assert "first_name" in patient
        assert "last_name" in patient
        assert "email" in patient

    @pytest.mark.asyncio
    async def test_get_patients_with_search(
        self, client: AsyncClient, auth_headers, test_patient
    ):
        """Test getting patients with search parameter"""
        # Endpoint uses ?query= for search
        response = await client.get(
            "/api/v1/patients?query=Doe", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1

        # Should find the test patient
        found = next(
            (p for p in data["items"] if p["first_name"] == "John"),
            None,
        )
        assert found is not None

    @pytest.mark.asyncio
    async def test_get_patients_with_pagination(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting patients with pagination parameters"""
        response = await client.get(
            "/api/v1/patients?page=1&limit=10", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_patients_unauthorized(self, client: AsyncClient):
        """Test getting patients without authentication"""
        response = await client.get("/api/v1/patients")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_patient_by_id_success(
        self, client: AsyncClient, auth_headers, test_patient
    ):
        """Test getting patient by ID"""
        response = await client.get(
            f"/api/v1/patients/{test_patient.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert str(data["id"]) == str(test_patient.id)
        assert data["first_name"] == test_patient.first_name
        assert data["last_name"] == test_patient.last_name
        assert data["email"] == test_patient.email

    @pytest.mark.asyncio
    async def test_get_patient_by_id_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Non-existent UUID returns 404"""
        missing_id = uuid_lib.uuid4()
        response = await client.get(
            f"/api/v1/patients/{missing_id}", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_patient_success(
        self, client: AsyncClient, auth_headers, test_patient
    ):
        """Test creating a new patient"""
        # Use a random email/phone to avoid collision with the test_patient fixture
        suffix = uuid_lib.uuid4().hex[:8]
        patient_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": f"jane.smith.{suffix}@example.com",
            "phone": f"+1555{suffix[:7]}",
            "date_of_birth": "1985-05-15",
            "gender": "female",
            "address_street": "456 Oak Ave",
            "address_city": "Springfield",
            "address_state": "IL",
            "address_zip": "62702",
            "emergency_contact": {
                "name": "John Smith",
                "relationship": "spouse",
                "phone": "+1987654322",
            },
            "medical_alerts": ["Allergic to penicillin"],
            "status": "active",
        }

        response = await client.post(
            "/api/v1/patients", json=patient_data, headers=auth_headers
        )

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["first_name"] == patient_data["first_name"]
        assert data["last_name"] == patient_data["last_name"]
        assert data["email"] == patient_data["email"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_patient_validation_error(
        self, client: AsyncClient, auth_headers
    ):
        """Test creating patient with invalid data rejects at validation"""
        patient_data = {
            "first_name": "",  # Empty name should fail validation
            "email": "invalid-email",  # Invalid email format
        }

        response = await client.post(
            "/api/v1/patients", json=patient_data, headers=auth_headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_email(
        self, client: AsyncClient, auth_headers, test_patient
    ):
        """Duplicate email or phone in same practice returns 409"""
        patient_data = {
            "first_name": "Another",
            "last_name": "Patient",
            "email": test_patient.email,  # Duplicate email
            "phone": "+1111111111",
            "date_of_birth": "1990-01-01",
            "gender": "male",
        }

        response = await client.post(
            "/api/v1/patients", json=patient_data, headers=auth_headers
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_patient_success(
        self, client: AsyncClient, auth_headers, test_patient, db_session: AsyncSession
    ):
        """Test updating a patient"""
        update_data = {
            "phone": "+1999999999",
            "address_street": "789 Pine St",
            "address_city": "Springfield",
            "address_state": "IL",
            "address_zip": "62703",
        }

        response = await client.put(
            f"/api/v1/patients/{test_patient.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["phone"] == update_data["phone"]
        assert data["address_street"] == update_data["address_street"]
        from app.core.search_index import hmac_index

        await db_session.refresh(test_patient)
        assert test_patient.search_index_phone == hmac_index(update_data["phone"])


    @pytest.mark.asyncio
    async def test_update_patient_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Updating non-existent patient returns 404"""
        missing_id = uuid_lib.uuid4()
        update_data = {"phone": "+1999999999"}

        response = await client.put(
            f"/api/v1/patients/{missing_id}",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_patient_success(
        self,
        client: AsyncClient,
        auth_headers,
        db_session: AsyncSession,
        test_practice,
    ):
        """Delete returns 204 No Content (soft delete to status=inactive)"""
        from app.models.patient import Patient

        patient = Patient(
            id=uuid_lib.uuid4(),
            practice_id=test_practice.id,
            first_name="Delete",
            last_name="Me",
            email=f"delete.me.{uuid_lib.uuid4().hex[:8]}@example.com",
            phone=f"+1{uuid_lib.uuid4().int % 10_000_000_000:010d}",
            date_of_birth=datetime.date(1990, 1, 1),
            gender="male",
            status="active",
        )
        db_session.add(patient)
        await db_session.commit()
        await db_session.refresh(patient)

        response = await client.delete(
            f"/api/v1/patients/{patient.id}", headers=auth_headers
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_patient_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Deleting non-existent patient returns 404"""
        missing_id = uuid_lib.uuid4()
        response = await client.delete(
            f"/api/v1/patients/{missing_id}", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_export_patient_data_success(
        self, client: AsyncClient, auth_headers, test_patient, db_session: AsyncSession
    ):
        """Test exporting patient data for GDPR/HIPAA compliance"""
        response = await client.get(
            f"/api/v1/patients/{test_patient.id}/export", headers=auth_headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert "exported_at" in data
        assert "exported_by" in data
        assert "patient_demographics" in data
        assert data["patient_demographics"]["id"] == str(test_patient.id)
        assert data["patient_demographics"]["first_name"] == test_patient.first_name
        assert "appointments" in data
        assert "clinical_notes" in data
        assert "treatment_plans" in data

        # Check that audit log was created
        from app.models.audit import AuditLog
        from sqlalchemy import select
        audit_result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.action == "patient_data_exported",
                AuditLog.entity_id == test_patient.id
            )
        )
        audit_log = audit_result.scalar_one_or_none()
        assert audit_log is not None
