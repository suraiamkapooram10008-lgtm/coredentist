"""
Comprehensive clinical endpoint tests.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinical import PerioChart, PerioChartEntry

pytestmark = pytest.mark.asyncio


class TestPerioChartEndpoints:
    """Authenticated perio chart CRUD tests."""

    async def test_list_perio_charts(self, client: AsyncClient, auth_headers, db_session, test_patient, test_user):
        chart = PerioChart(
            patient_id=test_patient.id,
            provider_id=test_user.id,
            overall_bleeding_index=15.5,
            diagnosis="Gingivitis",
        )
        db_session.add(chart)
        await db_session.commit()

        response = await client.get("/api/v1/clinical/perio/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(str(c["id"]) == str(chart.id) for c in data["perio_charts"])

    async def test_list_perio_charts_filter_by_patient(self, client: AsyncClient, auth_headers, db_session, test_patient, test_user):
        chart = PerioChart(
            patient_id=test_patient.id,
            provider_id=test_user.id,
            diagnosis="Healthy",
        )
        db_session.add(chart)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/clinical/perio/?patient_id={test_patient.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert all(str(c["patient_id"]) == str(test_patient.id) for c in data["perio_charts"])

    async def test_create_perio_chart(self, client: AsyncClient, auth_headers, test_patient):
        response = await client.post(
            "/api/v1/clinical/perio/",
            headers=auth_headers,
            json={
                "patient_id": str(test_patient.id),
                "overall_bleeding_index": 20.0,
                "plaque_index": 30.0,
                "diagnosis": "Periodontitis",
                "notes": "Moderate bone loss",
                "entries": [
                    {
                        "tooth_number": 1,
                        "pd_buccal": 3,
                        "pd_lingual": 4,
                        "bop_buccal": True,
                    }
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == str(test_patient.id)
        assert data["diagnosis"] == "Periodontitis"

    async def test_create_perio_chart_patient_not_found(self, client: AsyncClient, auth_headers):
        import uuid
        response = await client.post(
            "/api/v1/clinical/perio/",
            headers=auth_headers,
            json={
                "patient_id": str(uuid.uuid4()),
                "diagnosis": "Test",
                "entries": [],
            },
        )
        assert response.status_code == 404
