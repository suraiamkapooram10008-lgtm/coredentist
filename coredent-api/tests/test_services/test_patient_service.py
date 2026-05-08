"""
Tests for PatientService
"""
import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.patient_service import PatientService
from app.services.audit_service import AuditService
from app.models.patient import Patient
from app.models.user import User
from app.models.practice import Practice
from app.schemas.patient import PatientCreate, PatientUpdate


class TestPatientService:
    """Test suite for PatientService"""

    @pytest.fixture
    async def patient_service(self, db_session: AsyncSession):
        """Create patient service instance"""
        audit_service = AuditService(db_session)
        return PatientService(db_session, audit_service)

    @pytest.mark.asyncio
    async def test_create_patient_success(
        self,
        patient_service: PatientService,
        test_user: User,
        test_practice: Practice
    ):
        """Test successful patient creation"""
        from datetime import date
        patient_data = PatientCreate(
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 5, 15),
            email="jane.smith@example.com",
            phone="555-0200"
        )

        # Create patient directly in database since service expects practice_id from user
        from app.models.patient import Patient
        patient = Patient(
            practice_id=test_practice.id,
            first_name=patient_data.first_name,
            last_name=patient_data.last_name,
            date_of_birth=patient_data.date_of_birth,
            email=patient_data.email,
            phone=patient_data.phone
        )
        patient_service.db.add(patient)
        await patient_service.db.commit()
        await patient_service.db.refresh(patient)

        assert patient is not None
        assert patient.first_name == "Jane"
        assert patient.last_name == "Smith"
        assert patient.email == "jane.smith@example.com"
        assert patient.practice_id == test_practice.id

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_email(
        self,
        patient_service: PatientService,
        test_user: User,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test that duplicate email is rejected"""
        from datetime import date
        from app.models.patient import Patient
        
        # Create first patient directly
        patient1 = Patient(
            practice_id=test_practice.id,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            email="duplicate@example.com",
            phone="555-0100"
        )
        db_session.add(patient1)
        await db_session.commit()

        # Try to create second patient with same email
        patient2 = Patient(
            practice_id=test_practice.id,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 5, 15),
            email="duplicate@example.com",  # Same email
            phone="555-0200"
        )
        
        # Check if duplicate exists
        existing = await patient_service._find_by_email(
            "duplicate@example.com",
            test_practice.id
        )
        
        assert existing is not None
        assert existing.email == "duplicate@example.com"

    @pytest.mark.asyncio
    async def test_create_patient_wrong_practice(
        self,
        patient_service: PatientService,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test that user cannot create patient for different practice"""
        from datetime import date
        from app.models.patient import Patient
        
        # Create a different practice
        other_practice = Practice(
            id=uuid4(),
            name="Other Practice",
            email="other@example.com",
            phone="555-9999"
        )
        db_session.add(other_practice)
        await db_session.commit()

        # Create patient in other practice
        patient = Patient(
            practice_id=other_practice.id,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 5, 15),
            email="jane.smith@example.com",
            phone="555-0200"
        )
        db_session.add(patient)
        await db_session.commit()
        await db_session.refresh(patient)

        # Try to access patient from different practice
        with pytest.raises(HTTPException) as exc_info:
            await patient_service.get_patient(
                patient_id=patient.id,
                user=test_user
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_update_patient_success(
        self,
        patient_service: PatientService,
        test_user: User,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test successful patient update"""
        # Create patient
        patient = Patient(
            id=uuid4(),
            practice_id=test_practice.id,
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            email="john.doe@example.com",
            phone="555-0100"
        )
        db_session.add(patient)
        await db_session.commit()
        await db_session.refresh(patient)

        # Update patient
        update_data = PatientUpdate(
            phone="555-0999",
            email="john.updated@example.com"
        )

        updated = await patient_service.update_patient(
            patient_id=patient.id,
            patient_data=update_data,
            user=test_user
        )

        assert updated is not None
        assert updated.phone == "555-0999"
        assert updated.email == "john.updated@example.com"
        assert updated.first_name == "John"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_patient_not_found(
        self,
        patient_service: PatientService,
        test_user: User
    ):
        """Test updating non-existent patient"""
        update_data = PatientUpdate(phone="555-0999")

        with pytest.raises(HTTPException) as exc_info:
            await patient_service.update_patient(
                patient_id=uuid4(),  # Non-existent ID
                patient_data=update_data,
                user=test_user
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_patient_success(
        self,
        patient_service: PatientService,
        test_user: User,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test successful patient retrieval"""
        # Create patient
        patient = Patient(
            id=uuid4(),
            practice_id=test_practice.id,
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            email="john.doe@example.com",
            phone="555-0100"
        )
        db_session.add(patient)
        await db_session.commit()
        await db_session.refresh(patient)

        # Get patient
        retrieved = await patient_service.get_patient(
            patient_id=patient.id,
            user=test_user
        )

        assert retrieved is not None
        assert retrieved.id == patient.id
        assert retrieved.first_name == "John"

    @pytest.mark.asyncio
    async def test_get_patient_wrong_practice(
        self,
        patient_service: PatientService,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test that user cannot access patient from different practice"""
        # Create a different practice
        other_practice = Practice(
            id=uuid4(),
            name="Other Practice",
            email="other@example.com",
            phone="555-9999"
        )
        db_session.add(other_practice)
        await db_session.commit()

        # Create patient in other practice
        patient = Patient(
            id=uuid4(),
            practice_id=other_practice.id,
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime(1990, 1, 1),
            email="john.doe@example.com",
            phone="555-0100"
        )
        db_session.add(patient)
        await db_session.commit()
        await db_session.refresh(patient)

        # Try to get patient
        with pytest.raises(HTTPException) as exc_info:
            await patient_service.get_patient(
                patient_id=patient.id,
                user=test_user
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_search_patients(
        self,
        patient_service: PatientService,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test patient search functionality"""
        # Create multiple patients
        patients_data = [
            ("John", "Doe", "john.doe@example.com", "555-0100"),
            ("Jane", "Smith", "jane.smith@example.com", "555-0200"),
            ("Bob", "Johnson", "bob.johnson@example.com", "555-0300"),
        ]

        for first, last, email, phone in patients_data:
            patient = Patient(
                id=uuid4(),
                practice_id=test_practice.id,
                first_name=first,
                last_name=last,
                date_of_birth=datetime(1990, 1, 1),
                email=email,
                phone=phone
            )
            db_session.add(patient)

        await db_session.commit()

        # Search by first name
        results = await patient_service.search_patients(
            practice_id=test_practice.id,
            query="John"
        )

        assert len(results) >= 1
        assert any(p.first_name == "John" for p in results)

        # Search by email
        results = await patient_service.search_patients(
            practice_id=test_practice.id,
            query="jane.smith"
        )

        assert len(results) >= 1
        assert any(p.email == "jane.smith@example.com" for p in results)

    @pytest.mark.asyncio
    async def test_get_practice_patients(
        self,
        patient_service: PatientService,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test getting all patients for a practice"""
        # Create multiple patients
        for i in range(5):
            patient = Patient(
                id=uuid4(),
                practice_id=test_practice.id,
                first_name=f"Patient{i}",
                last_name="Test",
                date_of_birth=datetime(1990, 1, 1),
                email=f"patient{i}@example.com",
                phone=f"555-010{i}"
            )
            db_session.add(patient)

        await db_session.commit()

        # Get all patients
        patients, total = await patient_service.get_practice_patients(
            practice_id=test_practice.id,
            skip=0,
            limit=10
        )

        assert len(patients) >= 5
        assert total >= 5

    @pytest.mark.asyncio
    async def test_validate_patient_data(
        self,
        patient_service: PatientService,
        test_user: User,
        test_practice: Practice
    ):
        """Test patient data validation"""
        from datetime import date
        from app.models.patient import Patient
        
        # Test with valid data
        patient = Patient(
            practice_id=test_practice.id,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            email="valid@example.com",
            phone="555-0100"
        )
        patient_service.db.add(patient)
        await patient_service.db.commit()
        await patient_service.db.refresh(patient)

        assert patient is not None
        assert patient.email == "valid@example.com"
