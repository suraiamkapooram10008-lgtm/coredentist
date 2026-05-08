"""
Tests for appointment endpoints
"""
import pytest
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAppointmentEndpoints:
    """Test appointment management endpoints"""

    @pytest.mark.asyncio
    async def test_get_appointments_success(self, client: AsyncClient, auth_headers, test_appointment):
        """Test getting appointments list"""
        response = await client.get("/api/v1/appointments", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "appointments" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_get_appointments_with_date_filter(self, client: AsyncClient, auth_headers):
        """Test getting appointments with date filter"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = await client.get(f"/api/v1/appointments?start_date={today}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "appointments" in data

    @pytest.mark.asyncio
    async def test_get_appointments_unauthorized(self, client: AsyncClient):
        """Test getting appointments without authentication"""
        response = await client.get("/api/v1/appointments")

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_appointment_by_id_success(self, client: AsyncClient, auth_headers, test_appointment):
        """Test getting appointment by ID"""
        response = await client.get(f"/api/v1/appointments/{test_appointment.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert str(data["id"]) == str(test_appointment.id)
        assert str(data["patient_id"]) == str(test_appointment.patient_id)
        assert str(data["provider_id"]) == str(test_appointment.provider_id)
        assert data["appointment_type"] == test_appointment.appointment_type

    @pytest.mark.asyncio
    async def test_get_appointment_by_id_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent appointment"""
        nonexistent_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/appointments/{nonexistent_id}", headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_appointment_success(self, client: AsyncClient, auth_headers, test_patient, test_user):
        """Test creating new appointment"""
        start_time = (datetime.now() + timedelta(days=1)).isoformat()
        end_time = (datetime.now() + timedelta(days=1, hours=1)).isoformat()

        appointment_data = {
            "patient_id": str(test_patient.id),
            "provider_id": str(test_user.id),
            "appointment_type": "exam",  # Changed from "checkup" to valid enum value
            "start_time": start_time,
            "end_time": end_time,
            "notes": "Regular exam appointment"
        }

        response = await client.post("/api/v1/appointments", json=appointment_data, headers=auth_headers)

        assert response.status_code in [200, 201]
        data = response.json()
        assert str(data["patient_id"]) == appointment_data["patient_id"]
        assert str(data["provider_id"]) == appointment_data["provider_id"]
        assert data["appointment_type"] == appointment_data["appointment_type"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_appointment_validation_error(self, client: AsyncClient, auth_headers):
        """Test creating appointment with invalid data"""
        appointment_data = {
            "patient_id": "",  # Empty patient ID
            "start_time": "invalid-date"  # Invalid date format
        }

        response = await client.post("/api/v1/appointments", json=appointment_data, headers=auth_headers)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_appointment_time_conflict(self, client: AsyncClient, auth_headers, test_appointment, test_user):
        """Test creating appointment with time conflict"""
        # Try to create appointment at same time as existing one
        appointment_data = {
            "patient_id": str(test_appointment.patient_id),
            "provider_id": str(test_user.id),
            "appointment_type": "cleaning",
            "status": "scheduled",
            "start_time": test_appointment.start_time.isoformat(),
            "end_time": test_appointment.end_time.isoformat(),
            "duration": 60
        }

        response = await client.post("/api/v1/appointments", json=appointment_data, headers=auth_headers)

        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_appointment_success(self, client: AsyncClient, auth_headers, test_appointment):
        """Test updating appointment"""
        update_data = {
            "status": "confirmed",
            "notes": "Updated appointment notes"
        }

        response = await client.put(f"/api/v1/appointments/{test_appointment.id}",
                            json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == update_data["status"]
        assert data["notes"] == update_data["notes"]

    @pytest.mark.asyncio
    async def test_update_appointment_not_found(self, client: AsyncClient, auth_headers):
        """Test updating non-existent appointment"""
        nonexistent_id = str(uuid.uuid4())
        update_data = {"status": "confirmed"}

        response = await client.put(f"/api/v1/appointments/{nonexistent_id}",
                            json=update_data, headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_appointment_success(self, client: AsyncClient, auth_headers, db_session: AsyncSession, test_patient, test_user):
        """Test deleting appointment (soft delete by cancelling)"""
        # Create appointment to delete
        from app.models.appointment import Appointment

        appointment = Appointment(
            practice_id=test_user.practice_id,
            patient_id=test_patient.id,
            provider_id=test_user.id,
            appointment_type="consultation",
            status="scheduled",
            start_time=datetime.now() + timedelta(days=3),
            end_time=datetime.now() + timedelta(days=3, hours=1),
            duration=60
        )
        db_session.add(appointment)
        await db_session.commit()
        await db_session.refresh(appointment)

        response = await client.delete(f"/api/v1/appointments/{appointment.id}", headers=auth_headers)

        assert response.status_code == 200
        assert "cancelled" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_appointment_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting non-existent appointment"""
        nonexistent_id = str(uuid.uuid4())
        response = await client.delete(f"/api/v1/appointments/{nonexistent_id}", headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_available_slots(self, client: AsyncClient, auth_headers):
        """Test getting available appointment slots"""
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        response = await client.get(
            f"/api/v1/appointments/slots/available?date={date}&duration=30",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]
