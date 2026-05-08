"""
Tests for Prescription Management endpoints
"""
import pytest
from httpx import AsyncClient
import uuid

class TestPrescriptionEndpoints:
    """Test e-prescribing module endpoints"""

    @pytest.mark.asyncio
    async def test_list_prescriptions_empty(self, client: AsyncClient, auth_headers):
        """Test listing prescriptions when none exist"""
        response = await client.get("/api/v1/prescriptions/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "prescriptions" in data
        assert isinstance(data["prescriptions"], list)

    @pytest.mark.asyncio
    async def test_check_interactions(self, client: AsyncClient, auth_headers, test_patient):
        """Test the drug-drug interaction checker"""
        payload = {
            "patient_id": str(test_patient.id),
            "medication_name": "Amoxicillin"
        }
        response = await client.post("/api/v1/prescriptions/medications/check-interactions", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "interactions" in data
        assert "allergy_warnings" in data

    @pytest.mark.asyncio
    async def test_create_prescription_success(self, client: AsyncClient, auth_headers, test_patient):
        """Test creating a prescription successfully"""
        rx_data = {
            "patient_id": str(test_patient.id),
            "medication_id": None,
            "medication_name": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "tid",
            "route": "oral",
            "quantity": 30,
            "refills": 0,
            "sig": "Take one capsule three times daily",
            "dispense_as_written": False
        }
        response = await client.post("/api/v1/prescriptions/", json=rx_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["medication_name"] == "Amoxicillin"
        assert data["status"] == "draft"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_prescription_unauthorized(self, client: AsyncClient, test_patient):
        """Test creating a prescription without auth"""
        rx_data = {
            "patient_id": str(test_patient.id),
            "drug_name": "Lisinopril",
            "dosage": "10mg"
        }
        response = await client.post("/api/v1/prescriptions/", json=rx_data)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_templates(self, client: AsyncClient, auth_headers):
        """Test fetching prescription templates"""
        response = await client.get("/api/v1/prescriptions/templates/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)
