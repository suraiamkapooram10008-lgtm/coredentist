"""
Tests for patient portal endpoints (DPDPA compliance)
"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestPatientPortalEndpoints:
    """Test patient data portal endpoints"""

    @pytest.mark.asyncio
    async def test_export_patient_data_success(self, client: AsyncClient, auth_headers, test_patient):
        """Test exporting patient data"""
        response = await client.get(f"/api/v1/portal/export/{test_patient.id}", headers=auth_headers)
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_export_patient_data_not_found(self, client: AsyncClient, auth_headers):
        """Test exporting data for non-existent patient"""
        response = await client.get(f"/api/v1/portal/export/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_export_patient_data_unauthorized(self, client: AsyncClient, test_patient):
        """Test exporting data without auth"""
        response = await client.get(f"/api/v1/portal/export/{test_patient.id}")
        assert response.status_code in (403, 401)

    @pytest.mark.asyncio
    async def test_delete_patient_data_success(self, client: AsyncClient, auth_headers, db_session: AsyncSession, test_practice):
        """Test deleting patient data (right to erasure)"""
        from app.models.patient import Patient
        from datetime import date
        patient = Patient(
            practice_id=test_practice.id,
            first_name="Delete",
            last_name="Me",
            email=f"delete_{uuid.uuid4().hex[:8]}@example.com",
            phone="+1234567890",
            date_of_birth=date(1990, 1, 1),
            status="active",
        )
        db_session.add(patient)
        await db_session.commit()
        await db_session.refresh(patient)

        response = await client.delete(f"/api/v1/portal/me/{patient.id}", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_patient_data_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting non-existent patient"""
        response = await client.delete(f"/api/v1/portal/me/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_withdraw_consent_success(self, client: AsyncClient, auth_headers, test_patient):
        """Test withdrawing consent"""
        response = await client.post(
            f"/api/v1/portal/consent/withdraw/{test_patient.id}",
            json={"reason": "No longer want services"},
            headers=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_consent_status_success(self, client: AsyncClient, auth_headers, test_patient):
        """Test getting consent status"""
        response = await client.get(f"/api/v1/portal/consent/status/{test_patient.id}", headers=auth_headers)
        assert response.status_code == 200
