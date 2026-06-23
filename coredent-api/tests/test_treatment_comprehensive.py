"""
Comprehensive treatment planning endpoint tests.
"""
import datetime
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.treatment import TreatmentPlan, TreatmentPlanStatus, TreatmentPhase, TreatmentProcedure

pytestmark = pytest.mark.asyncio


class TestTreatmentPlanCRUD:
    """Authenticated treatment plan lifecycle tests."""

    async def test_list_treatment_plans(self, client: AsyncClient, auth_headers, db_session, test_patient, test_practice, test_user):
        plan = TreatmentPlan(
            practice_id=test_practice.id,
            patient_id=test_patient.id,
            provider_id=test_user.id,
            plan_name="Cleaning Plan",
            status=TreatmentPlanStatus.DRAFT,
        )
        db_session.add(plan)
        await db_session.commit()

        response = await client.get("/api/v1/treatment/plans/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(p["plan_name"] == "Cleaning Plan" for p in data["plans"])

    async def test_create_treatment_plan(self, client: AsyncClient, auth_headers, test_patient, test_user):
        response = await client.post(
            "/api/v1/treatment/plans/",
            headers=auth_headers,
            json={
                "patient_id": str(test_patient.id),
                "provider_id": str(test_user.id),
                "plan_name": "Comprehensive Restoration",
                "status": "draft",
                "chief_complaint": "Multiple cavities",
                "notes": "Patient anxious",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan_name"] == "Comprehensive Restoration"
        assert data["patient_id"] == str(test_patient.id)
        assert data["status"] == "draft"

    async def test_create_treatment_plan_patient_not_found(self, client: AsyncClient, auth_headers, test_user):
        response = await client.post(
            "/api/v1/treatment/plans/",
            headers=auth_headers,
            json={
                "patient_id": str(uuid.uuid4()),
                "provider_id": str(test_user.id),
                "plan_name": "Ghost Plan",
            },
        )
        assert response.status_code == 404

    async def test_get_treatment_plan(self, client: AsyncClient, auth_headers, db_session, test_patient, test_practice, test_user):
        plan = TreatmentPlan(
            practice_id=test_practice.id,
            patient_id=test_patient.id,
            provider_id=test_user.id,
            plan_name="Extraction Plan",
            status=TreatmentPlanStatus.DRAFT,
        )
        db_session.add(plan)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/treatment/plans/{plan.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(plan.id)
        assert data["plan_name"] == "Extraction Plan"

    async def test_update_treatment_plan(self, client: AsyncClient, auth_headers, db_session, test_patient, test_practice, test_user):
        plan = TreatmentPlan(
            practice_id=test_practice.id,
            patient_id=test_patient.id,
            provider_id=test_user.id,
            plan_name="Old Plan",
            status=TreatmentPlanStatus.DRAFT,
        )
        db_session.add(plan)
        await db_session.commit()

        response = await client.put(
            f"/api/v1/treatment/plans/{plan.id}",
            headers=auth_headers,
            json={"plan_name": "Updated Plan", "status": "in_progress"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan_name"] == "Updated Plan"
        assert data["status"] == "in_progress"

    async def test_delete_treatment_plan(self, client: AsyncClient, auth_headers, db_session, test_patient, test_practice, test_user):
        plan = TreatmentPlan(
            practice_id=test_practice.id,
            patient_id=test_patient.id,
            provider_id=test_user.id,
            plan_name="Delete Plan",
            status=TreatmentPlanStatus.DRAFT,
        )
        db_session.add(plan)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/treatment/plans/{plan.id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert "cancelled" in response.json()["message"].lower()


class TestTreatmentPlanPhases:
    """Treatment phase endpoint tests."""

    async def test_list_phases(self, client: AsyncClient, auth_headers, db_session, test_patient, test_practice, test_user):
        plan = TreatmentPlan(
            practice_id=test_practice.id,
            patient_id=test_patient.id,
            provider_id=test_user.id,
            plan_name="Phase Plan",
            status=TreatmentPlanStatus.DRAFT,
        )
        db_session.add(plan)
        await db_session.flush()

        phase = TreatmentPhase(
            treatment_plan_id=plan.id,
            phase_name="Phase 1",
            phase_number=1,
            status="active",
        )
        db_session.add(phase)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/treatment/plans/{plan.id}/phases", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(p["phase_name"] == "Phase 1" for p in data["phases"])

    async def test_create_phase(self, client: AsyncClient, auth_headers, db_session, test_patient, test_practice, test_user):
        plan = TreatmentPlan(
            practice_id=test_practice.id,
            patient_id=test_patient.id,
            provider_id=test_user.id,
            plan_name="Phase Create Plan",
            status=TreatmentPlanStatus.DRAFT,
        )
        db_session.add(plan)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/treatment/plans/{plan.id}/phases",
            headers=auth_headers,
            json={
                "phase_name": "Initial Phase",
                "phase_number": 1,
                "description": "First phase of treatment",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phase_name"] == "Initial Phase"
        assert data["treatment_plan_id"] == str(plan.id)
