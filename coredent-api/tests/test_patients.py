"""
Tests for patient endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestPatientEndpoints:
    """Test patient management endpoints"""

    def test_get_patients_success(self, client: TestClient, auth_headers, test_patient):
        """Test getting patients list"""
        response = client.get("/api/v1/patients", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["data"]) >= 1
        
        # Check patient data structure
        patient = data["data"][0]
        assert "id" in patient
        assert "first_name" in patient
        assert "last_name" in patient
        assert "email" in patient

    def test_get_patients_with_search(self, client: TestClient, auth_headers, test_patient):
        """Test getting patients with search parameter"""
        response = client.get("/api/v1/patients?search=John", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        
        # Should find the test patient
        found_patient = next((p for p in data["data"] if p["first_name"] == "John"), None)
        assert found_patient is not None

    def test_get_patients_with_pagination(self, client: TestClient, auth_headers):
        """Test getting patients with pagination"""
        response = client.get("/api/v1/patients?page=1&page_size=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_get_patients_unauthorized(self, client: TestClient):
        """Test getting patients without authentication"""
        response = client.get("/api/v1/patients")
        
        assert response.status_code == 401

    def test_get_patient_by_id_success(self, client: TestClient, auth_headers, test_patient):
        """Test getting patient by ID"""
        response = client.get(f"/api/v1/patients/{test_patient.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_patient.id
        assert data["first_name"] == test_patient.first_name
        assert data["last_name"] == test_patient.last_name
        assert data["email"] == test_patient.email

    def test_get_patient_by_id_not_found(self, client: TestClient, auth_headers):
        """Test getting non-existent patient"""
        response = client.get("/api/v1/patients/nonexistent-id", headers=auth_headers)
        
        assert response.status_code == 404

    def test_create_patient_success(self, client: TestClient, auth_headers):
        """Test creating new patient"""
        patient_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "+1987654321",
            "date_of_birth": "1985-05-15",
            "gender": "female",
            "address": {
                "street": "456 Oak Ave",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62702",
                "country": "USA"
            },
            "emergency_contact": {
                "name": "John Smith",
                "relationship": "spouse",
                "phone": "+1987654322"
            },
            "medical_alerts": ["Allergic to penicillin"],
            "status": "active"
        }
        
        response = client.post("/api/v1/patients", json=patient_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == patient_data["first_name"]
        assert data["last_name"] == patient_data["last_name"]
        assert data["email"] == patient_data["email"]
        assert "id" in data
        assert "created_at" in data

    def test_create_patient_validation_error(self, client: TestClient, auth_headers):
        """Test creating patient with invalid data"""
        patient_data = {
            "first_name": "",  # Empty name should fail validation
            "email": "invalid-email"  # Invalid email format
        }
        
        response = client.post("/api/v1/patients", json=patient_data, headers=auth_headers)
        
        assert response.status_code == 422

    def test_create_patient_duplicate_email(self, client: TestClient, auth_headers, test_patient):
        """Test creating patient with duplicate email"""
        patient_data = {
            "first_name": "Another",
            "last_name": "Patient",
            "email": test_patient.email,  # Duplicate email
            "phone": "+1111111111",
            "date_of_birth": "1990-01-01",
            "gender": "male"
        }
        
        response = client.post("/api/v1/patients", json=patient_data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_update_patient_success(self, client: TestClient, auth_headers, test_patient):
        """Test updating patient"""
        update_data = {
            "phone": "+1999999999",
            "address": {
                "street": "789 Pine St",
                "city": "Springfield",
                "state": "IL",
                "zip_code": "62703",
                "country": "USA"
            }
        }
        
        response = client.put(f"/api/v1/patients/{test_patient.id}", 
                            json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == update_data["phone"]
        assert data["address"]["street"] == update_data["address"]["street"]

    def test_update_patient_not_found(self, client: TestClient, auth_headers):
        """Test updating non-existent patient"""
        update_data = {"phone": "+1999999999"}
        
        response = client.put("/api/v1/patients/nonexistent-id", 
                            json=update_data, headers=auth_headers)
        
        assert response.status_code == 404

    def test_delete_patient_success(self, client: TestClient, auth_headers, db_session):
        """Test deleting patient"""
        # Create a patient to delete
        from app.models.patient import Patient
        patient = Patient(
            first_name="Delete",
            last_name="Me",
            email="delete.me@example.com",
            phone="+1000000000",
            date_of_birth="1990-01-01",
            gender="male",
            status="active"
        )
        db_session.add(patient)
        db_session.commit()
        db_session.refresh(patient)
        
        response = client.delete(f"/api/v1/patients/{patient.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_patient_not_found(self, client: TestClient, auth_headers):
        """Test deleting non-existent patient"""
        response = client.delete("/api/v1/patients/nonexistent-id", headers=auth_headers)
        
        assert response.status_code == 404

    def test_delete_patient_with_appointments(self, client: TestClient, auth_headers, test_appointment):
        """Test deleting patient with active appointments"""
        patient_id = test_appointment.patient_id
        
        response = client.delete(f"/api/v1/patients/{patient_id}", headers=auth_headers)
        
        # Should prevent deletion if patient has appointments
        assert response.status_code == 400
        assert "appointments" in response.json()["detail"].lower()

    def test_get_patient_appointments(self, client: TestClient, auth_headers, test_appointment):
        """Test getting patient's appointments"""
        patient_id = test_appointment.patient_id
        
        response = client.get(f"/api/v1/patients/{patient_id}/appointments", 
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["patient_id"] == patient_id

    def test_get_patient_medical_history(self, client: TestClient, auth_headers, test_patient):
        """Test getting patient's medical history"""
        response = client.get(f"/api/v1/patients/{test_patient.id}/medical-history", 
                            headers=auth_headers)
        
        assert response.status_code == 200
        # Medical history structure would depend on implementation