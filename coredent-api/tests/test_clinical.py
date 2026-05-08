"""
Tests for clinical endpoints (perio charting)
"""
import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestClinicalEndpoints:
    """Test clinical record endpoints"""

    @pytest.mark.asyncio
    async def test_list_perio_charts_empty(self, client: AsyncClient, auth_headers):
        """Test listing perio charts when none exist"""
        response = await client.get("/api/v1/clinical/perio/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["perio_charts"] == []

    @pytest.mark.asyncio
    async def test_create_perio_chart_success(self, client: AsyncClient, auth_headers, test_patient):
        """Test creating a perio chart"""
        chart_data = {
            "patient_id": str(test_patient.id),
            "overall_bleeding_index": 0.5,
            "plaque_index": 1.2,
            "calculus_index": 0.8,
            "diagnosis": "Mild gingivitis",
            "notes": "First examination",
            "entries": [
                {
                    "tooth_number": "1",
                    "probing_depths": [3, 2, 3, 4, 3, 2],
                    "bleeding_points": [True, False, True, False, True, False],
                    "mobility": "0",
                }
            ]
        }
        response = await client.post("/api/v1/clinical/perio/", json=chart_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == str(test_patient.id)
        assert data["diagnosis"] == "Mild gingivitis"

    @pytest.mark.asyncio
    async def test_create_perio_chart_unauthorized(self, client: AsyncClient, test_patient):
        """Test creating perio chart without auth"""
        chart_data = {
            "patient_id": str(test_patient.id),
            "entries": []
        }
        response = await client.post("/api/v1/clinical/perio/", json=chart_data)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_perio_chart_invalid_patient(self, client: AsyncClient, auth_headers):
        """Test creating perio chart for non-existent patient"""
        chart_data = {
            "patient_id": str(uuid.uuid4()),
            "entries": []
        }
        response = await client.post("/api/v1/clinical/perio/", json=chart_data, headers=auth_headers)
        assert response.status_code == 404

