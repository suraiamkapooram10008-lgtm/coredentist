"""
Tests for appointment endpoints
"""
import pytest
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
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check appointment data structure
        appointment = data[0]
        assert "id" in appointment
        assert "patient_id" in appointment
        assert "provider_id" in appointment
        assert "appointment_type" in appointment
        assert "status" in appointment
        assert "start_time" in appointment
        assert "end_time" in appointment

    @pytest.mark.asyncio
    async def test_get_appointments_with_date_filter(self, client: AsyncClient, auth_headers):
        """Test getting appointments with date filter"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = await client.get(f"/api/v1/appointments?date={today}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_appointments_with_status_filter(self, client: AsyncClient, auth_headers):
        """Test getting appointments with status filter"""
        response = await client.get("/api/v1/appointments?status=scheduled", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_appointments_unauthorized(self, client: AsyncClient):
        """Test getting appointments without authentication"""
        response = await client.get("/api/v1/appointments")
        
        assert response.status_code == 401

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
        response = await client.get("/api/v1/appointments/nonexistent-id", headers=auth_headers)
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_appointment_success(self, client: AsyncClient, auth_headers, test_patient, test_user):
        """Test creating new appointment"""
        start_time = (datetime.now() + timedelta(days=1)).isoformat()
        end_time = (datetime.now() + timedelta(days=1, hours=1)).isoformat()
        
        appointment_data = {
            "patient_id": str(test_patient.id),
            "provider_id": str(test_user.id),
            "appointment_type": "checkup",
            "status": "scheduled",
            "start_time": start_time,
            "end_time": end_time,
            "duration": 60,
            "notes": "Regular checkup appointment",
            "chair_id": "chair-1"
        }
        
        response = await client.post("/api/v1/appointments", json=appointment_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert str(data["patient_id"]) == appointment_data["patient_id"]
        assert str(data["provider_id"]) == appointment_data["provider_id"]
        assert data["appointment_type"] == appointment_data["appointment_type"]
        assert "id" in data
        assert "created_at" in data

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
        
        assert response.status_code == 400
        assert "conflict" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_appointment_success(self, client: AsyncClient, auth_headers, test_appointment):
        """Test updating appointment"""
        update_data = {
            "status": "confirmed",
            "notes": "Updated appointment notes",
            "duration": 90
        }
        
        response = await client.put(f"/api/v1/appointments/{test_appointment.id}", 
                            json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == update_data["status"]
        assert data["notes"] == update_data["notes"]
        assert data["duration"] == update_data["duration"]

    @pytest.mark.asyncio
    async def test_update_appointment_not_found(self, client: AsyncClient, auth_headers):
        """Test updating non-existent appointment"""
        update_data = {"status": "confirmed"}
        
        response = await client.put("/api/v1/appointments/nonexistent-id", 
                            json=update_data, headers=auth_headers)
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_appointment_success(self, client: AsyncClient, auth_headers, test_appointment):
        """Test canceling appointment"""
        cancel_data = {
            "reason": "Patient requested cancellation",
            "cancelled_by": "patient"
        }
        
        response = await client.post(f"/api/v1/appointments/{test_appointment.id}/cancel", 
                             json=cancel_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["cancellation_reason"] == cancel_data["reason"]

    @pytest.mark.asyncio
    async def test_reschedule_appointment_success(self, client: AsyncClient, auth_headers, test_appointment):
        """Test rescheduling appointment"""
        new_start_time = (datetime.now() + timedelta(days=2)).isoformat()
        new_end_time = (datetime.now() + timedelta(days=2, hours=1)).isoformat()
        
        reschedule_data = {
            "start_time": new_start_time,
            "end_time": new_end_time,
            "reason": "Patient requested reschedule"
        }
        
        response = await client.post(f"/api/v1/appointments/{test_appointment.id}/reschedule", 
                             json=reschedule_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["start_time"] == new_start_time
        assert data["end_time"] == new_end_time

    @pytest.mark.asyncio
    async def test_complete_appointment_success(self, client: AsyncClient, auth_headers, test_appointment):
        """Test completing appointment"""
        completion_data = {
            "treatment_notes": "Cleaning completed successfully",
            "next_appointment_recommended": True,
            "next_appointment_interval": "6 months"
        }
        
        response = await client.post(f"/api/v1/appointments/{test_appointment.id}/complete", 
                             json=completion_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["treatment_notes"] == completion_data["treatment_notes"]

    @pytest.mark.asyncio
    async def test_delete_appointment_success(self, client: AsyncClient, auth_headers, db_session: AsyncSession, test_patient, test_user):
        """Test deleting appointment"""
        # Create appointment to delete
        from app.models.appointment import Appointment
        import uuid as uuid_lib
        
        appointment = Appointment(
            id=uuid_lib.uuid4(),
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
        assert "deleted" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_appointment_not_found(self, client: AsyncClient, auth_headers):
        """Test deleting non-existent appointment"""
        response = await client.delete("/api/v1/appointments/nonexistent-id", headers=auth_headers)
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_appointment_availability(self, client: AsyncClient, auth_headers):
        """Test getting available appointment slots"""
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = await client.get(f"/api/v1/appointments/availability?date={date}&provider_id=provider-1", 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "available_slots" in data
        assert isinstance(data["available_slots"], list)

    @pytest.mark.asyncio
    async def test_get_appointment_conflicts(self, client: AsyncClient, auth_headers, test_appointment):
        """Test checking for appointment conflicts"""
        conflict_data = {
            "start_time": test_appointment.start_time.isoformat(),
            "end_time": test_appointment.end_time.isoformat(),
            "provider_id": str(test_appointment.provider_id)
        }
        
        response = await client.post("/api/v1/appointments/check-conflicts", 
                             json=conflict_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "conflicts" in data
        assert len(data["conflicts"]) >= 1  # Should find the existing appointment
