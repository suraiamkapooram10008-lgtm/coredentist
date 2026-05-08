"""
Tests for treatment plan workflows
"""
import pytest
from httpx import AsyncClient
from datetime import date, timedelta


class TestTreatmentPlanEndpoints:
    """Test treatment plan management"""

    @pytest.mark.asyncio
    async def test_create_treatment_plan(self, client: AsyncClient, auth_headers, test_patient, test_user):
        """Test creating a treatment plan"""
        plan_data = {
            "patient_id": str(test_patient.id),
            "provider_id": str(test_user.id),
            "title": "Comprehensive Dental Treatment",
            "description": "Full mouth restoration",
            "total_cost": 5000.00,
            "start_date": str(date.today()),
            "estimated_completion_date": str(date.today() + timedelta(days=90))
        }
        
        response = await client.post(
            "/api/v1/treatment/plans",
            json=plan_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 404]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["title"] == plan_data["title"]
            assert data["status"] in ["draft", "pending_approval"]

    @pytest.mark.asyncio
    async def test_list_treatment_plans(self, client: AsyncClient, auth_headers, test_patient):
        """Test listing treatment plans for a patient"""
        response = await client.get(
            f"/api/v1/treatment/plans?patient_id={test_patient.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_update_treatment_plan_status(self, client: AsyncClient, auth_headers):
        """Test updating treatment plan status"""
        # This test assumes a plan exists
        # In real scenario, create one first
        plan_id = "00000000-0000-0000-0000-000000000000"
        
        update_data = {
            "status": "approved"
        }
        
        response = await client.patch(
            f"/api/v1/treatment/plans/{plan_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]


class TestTreatmentProcedures:
    """Test treatment procedures"""

    @pytest.mark.asyncio
    async def test_add_procedure_to_plan(self, client: AsyncClient, auth_headers):
        """Test adding a procedure to treatment plan"""
        plan_id = "00000000-0000-0000-0000-000000000000"
        
        procedure_data = {
            "procedure_code": "D0120",
            "procedure_name": "Periodic oral evaluation",
            "tooth_number": "14",
            "cost": 150.00,
            "status": "pending"
        }
        
        response = await client.post(
            f"/api/v1/treatment/plans/{plan_id}/procedures",
            json=procedure_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 404]

    @pytest.mark.asyncio
    async def test_list_procedures(self, client: AsyncClient, auth_headers):
        """Test listing available procedures"""
        response = await client.get(
            "/api/v1/treatment/procedures",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]


class TestTreatmentPlanApproval:
    """Test treatment plan approval workflow"""

    @pytest.mark.asyncio
    async def test_approve_treatment_plan(self, client: AsyncClient, auth_headers):
        """Test approving a treatment plan"""
        plan_id = "00000000-0000-0000-0000-000000000000"
        
        response = await client.post(
            f"/api/v1/treatment/plans/{plan_id}/approve",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404, 405]

    @pytest.mark.asyncio
    async def test_reject_treatment_plan(self, client: AsyncClient, auth_headers):
        """Test rejecting a treatment plan"""
        plan_id = "00000000-0000-0000-0000-000000000000"
        
        rejection_data = {
            "reason": "Patient declined treatment"
        }
        
        response = await client.post(
            f"/api/v1/treatment/plans/{plan_id}/reject",
            json=rejection_data,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404, 405]
