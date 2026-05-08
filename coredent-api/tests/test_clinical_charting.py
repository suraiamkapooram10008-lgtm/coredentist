"""
Tests for Visual Clinical Charting endpoints
"""
import pytest
from httpx import AsyncClient

class TestClinicalChartingEndpoints:
    """Test Visual Charting module endpoints"""

    @pytest.mark.asyncio
    async def test_get_patient_chart(self, client: AsyncClient, auth_headers, test_patient):
        """Test getting full patient chart"""
        response = await client.get(f"/api/v1/clinical/chart/{test_patient.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "chart_id" in data
        assert "conditions" in data
        assert isinstance(data["conditions"], list)

    @pytest.mark.asyncio
    async def test_add_tooth_condition(self, client: AsyncClient, auth_headers, test_patient):
        """Test adding a condition to a tooth"""
        condition_data = {
            "tooth_number": "14",
            "surface": "MOD",
            "condition_type": "caries",
            "status": "existing",
            "severity": "moderate",
            "notes": "Deep decay observed"
        }
        response = await client.post(
            f"/api/v1/clinical/chart/{test_patient.id}/conditions", 
            json=condition_data, 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tooth_number"] == "14"
        assert data["condition_type"] == "caries"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_chart_history(self, client: AsyncClient, auth_headers, test_patient):
        """Test retrieving the charting history log"""
        # Ensure a condition exists first
        condition_data = {
            "tooth_number": "8",
            "condition_type": "fracture"
        }
        await client.post(
            f"/api/v1/clinical/chart/{test_patient.id}/conditions", 
            json=condition_data, 
            headers=auth_headers
        )
        
        response = await client.get(f"/api/v1/clinical/chart/{test_patient.id}/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) > 0
        
        # Verify the entry exists
        found = False
        for entry in data["history"]:
            if entry["tooth_number"] == "8" and entry["entry_type"] == "condition":
                found = True
        assert found

    @pytest.mark.asyncio
    async def test_charting_symbols(self, client: AsyncClient, auth_headers):
        """Test creating and listing charting symbols"""
        symbol_data = {
            "name": "Implant Crown",
            "symbol_type": "crown",
            "category": "prosthetics",
            "color": "#FFD700"
        }
        # Create
        create_resp = await client.post("/api/v1/clinical/chart/symbols/", json=symbol_data, headers=auth_headers)
        assert create_resp.status_code == 200
        
        # List
        list_resp = await client.get("/api/v1/clinical/chart/symbols/", headers=auth_headers)
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert "symbols" in data
        assert len(data["symbols"]) > 0
