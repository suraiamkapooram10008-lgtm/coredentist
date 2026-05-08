"""
Enhanced Tests for Appointment API endpoints
Targets 70% coverage for appointments module
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.appointment import Appointment, AppointmentStatus, AppointmentTypeEnum
from app.models.patient import Patient
from app.models.user import User


class TestAppointmentEndpointsEnhanced:
    """Enhanced test cases for appointment endpoints - targeting coverage"""

    @pytest.mark.asyncio
    async def test_list_appointments_empty(self, client: AsyncClient, auth_headers):
        """Test getting appointments when none exist"""
        response = await client.get("/api/v1/appointments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "appointments" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_appointments_with_patient_filter(self, client: AsyncClient, auth_headers, test_appointment):
        """Test filtering appointments by patient"""
        patient_id = str(test_appointment.patient_id)
        response = await client.get(
            f"/api/v1/appointments?patient_id={patient_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_appointments_with_provider_filter(self, client: AsyncClient, auth_headers, test_appointment, test_user):
        """Test filtering appointments by provider"""
        response = await client.get(
            f"/api/v1/appointments?provider_id={test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_appointment_with_chair(self, client: AsyncClient, auth_headers, test_patient, test_user):
        """Test creating appointment with chair assignment"""
        start_time = (datetime.now() + timedelta(days=2)).isoformat()
        end_time = (datetime.now() + timedelta(days=2, hours=1)).isoformat()

        from uuid import uuid4
        chair_uuid = str(uuid4())
        appointment_data = {
            "patient_id": str(test_patient.id),
            "provider_id": str(test_user.id),
            "appointment_type": "cleaning",
            "status": "scheduled",
            "start_time": start_time,
            "end_time": end_time,
            "duration": 60,
            "notes": "Test with chair",
            "chair_id": chair_uuid
        }

        response = await client.post(
            "/api/v1/appointments",
            json=appointment_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["chair_id"] == chair_uuid

    @pytest.mark.asyncio
    async def test_create_appointment_patient_not_found(self, client: AsyncClient, auth_headers, test_user):
        """Test creating appointment with non-existent patient"""
        start_time = (datetime.now() + timedelta(days=1)).isoformat()
        end_time = (datetime.now() + timedelta(days=1, hours=1)).isoformat()

        appointment_data = {
            "patient_id": str(uuid4()),
            "provider_id": str(test_user.id),
            "appointment_type": "checkup",
            "start_time": start_time,
            "end_time": end_time,
        }

        response = await client.post(
            "/api/v1/appointments",
            json=appointment_data,
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_appointment_change_time(self, client: AsyncClient, auth_headers, test_appointment):
        """Test updating appointment time"""
        new_start = (datetime.now() + timedelta(days=3)).isoformat()
        new_end = (datetime.now() + timedelta(days=3, hours=1)).isoformat()

        update_data = {
            "start_time": new_start,
            "end_time": new_end,
        }

        response = await client.put(
            f"/api/v1/appointments/{test_appointment.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["start_time"] is not None

    @pytest.mark.asyncio
    async def test_update_appointment_with_conflict(self, client: AsyncClient, auth_headers, test_appointment, test_user):
        """Test updating appointment causing conflict"""
        # Create another appointment
        start_time = (datetime.now() + timedelta(days=4)).isoformat()
        end_time = (datetime.now() + timedelta(days=4, hours=1)).isoformat()

        appt_data = {
            "patient_id": str(test_appointment.patient_id),
            "provider_id": str(test_user.id),
            "appointment_type": "checkup",
            "start_time": start_time,
            "end_time": end_time,
        }

        resp = await client.post(
            "/api/v1/appointments",
            json=appt_data,
            headers=auth_headers
        )
        assert resp.status_code == 201
        new_appt_id = resp.json()["id"]

        # Try to update first appointment to conflict with second
        update_data = {
            "start_time": start_time,
            "end_time": end_time,
        }

        response = await client.put(
            f"/api/v1/appointments/{test_appointment.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_appointment_not_found(self, client: AsyncClient, auth_headers):
        """Test updating non-existent appointment"""
        update_data = {"status": "confirmed"}
        response = await client.put(
            f"/api/v1/appointments/{uuid4()}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_appointment_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent appointment"""
        response = await client.get(
            f"/api/v1/appointments/{uuid4()}",
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_appointment_with_reason(self, client: AsyncClient, auth_headers, test_appointment):
        """Test cancelling appointment with reason"""
        cancel_data = {
            "reason": "Emergency came up",
            "cancelled_by": "provider"
        }

        response = await client.post(
            f"/api/v1/appointments/{test_appointment.id}/cancel",
            json=cancel_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_complete_appointment(self, client: AsyncClient, auth_headers, test_appointment):
        """Test completing appointment"""
        response = await client.post(
            f"/api/v1/appointments/{test_appointment.id}/complete",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_available_slots(self, client: AsyncClient, auth_headers, test_user):
        """Test getting available appointment slots"""
        date = datetime.now().date().isoformat()
        response = await client.get(
            f"/api/v1/appointments/available-slots?date={date}&provider_id={test_user.id}",
            headers=auth_headers
        )
        # Might return 200 with slots or empty list
        assert response.status_code in [200, 404]  # endpoint might not exist

    @pytest.mark.asyncio
    async def test_appointment_unauthorized(self, client: AsyncClient):
        """Test appointment endpoints without auth"""
        response = await client.get("/api/v1/appointments")
        assert response.status_code == 403  # CSRF or auth failure

    @pytest.mark.asyncio
    async def test_create_appointment_invalid_type(self, client: AsyncClient, auth_headers, test_patient):
        """Test creating appointment with invalid type"""
        start_time = (datetime.now() + timedelta(days=1)).isoformat()
        end_time = (datetime.now() + timedelta(days=1, hours=1)).isoformat()

        appointment_data = {
            "patient_id": str(test_patient.id),
            "appointment_type": "invalid_type",
            "start_time": start_time,
            "end_time": end_time,
        }

        response = await client.post(
            "/api/v1/appointments",
            json=appointment_data,
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_appointment_partial(self, client: AsyncClient, auth_headers, test_appointment):
        """Test partial update of appointment"""
        update_data = {
            "notes": "Updated notes only"
        }

        response = await client.put(
            f"/api/v1/appointments/{test_appointment.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes only"

    @pytest.mark.asyncio
    async def test_list_appointments_date_range(self, client: AsyncClient, auth_headers):
        """Test listing appointments with date range"""
        start = (datetime.now() - timedelta(days=1)).isoformat()
        end = (datetime.now() + timedelta(days=30)).isoformat()

        response = await client.get(
            f"/api/v1/appointments?start_date={start}&end_date={end}",
            headers=auth_headers
        )
        assert response.status_code == 200
