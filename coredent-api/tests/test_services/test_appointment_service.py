"""
Tests for AppointmentService
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.user import User
from app.models.practice import Practice
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


class TestAppointmentService:
    """Test suite for AppointmentService"""

    @pytest.fixture
    async def appointment_service(self, db_session: AsyncSession):
        """Create appointment service instance"""
        audit_service = AuditService(db_session)
        return AppointmentService(db_session, audit_service)

    @pytest.mark.asyncio
    async def test_create_appointment_with_duration(
        self,
        appointment_service: AppointmentService,
        test_patient: Patient,
        test_user: User,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test creating appointment with automatic duration calculation"""
        from app.core.security import get_password_hash
        
        # Create a unique provider for this test
        provider = User(
            id=uuid4(),
            practice_id=test_practice.id,
            email=f"provider_{uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("secret"),
            role="dentist",
            first_name="Dr.",
            last_name="Smith",
            is_active=True,
            mfa_enabled=True,
            mfa_verified=True
        )
        db_session.add(provider)
        await db_session.commit()
        await db_session.refresh(provider)

        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        appointment_data = AppointmentCreate(
            patient_id=test_patient.id,
            provider_id=provider.id,
            start_time=start_time,
            end_time=end_time,
            appointment_type="exam"
        )

        appointment = await appointment_service.create_appointment(
            appointment_data=appointment_data,
            user=test_user
        )

        assert appointment is not None
        assert appointment.patient_id == test_patient.id
        assert appointment.provider_id == provider.id
        assert appointment.start_time == start_time
        assert appointment.end_time == end_time
        assert appointment.duration == 60  # 1 hour in minutes

    @pytest.mark.asyncio
    async def test_create_appointment_with_conflict(
        self,
        appointment_service: AppointmentService,
        test_patient: Patient,
        test_user: User,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test that conflicting appointments are detected"""
        from app.core.security import get_password_hash
        from fastapi import HTTPException
        
        # Create a unique provider
        provider = User(
            id=uuid4(),
            practice_id=test_practice.id,
            email=f"provider_{uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("secret"),
            role="dentist",
            first_name="Dr.",
            last_name="Smith",
            is_active=True,
            mfa_enabled=True,
            mfa_verified=True
        )
        db_session.add(provider)
        await db_session.commit()
        await db_session.refresh(provider)

        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        # Create first appointment
        appointment_data1 = AppointmentCreate(
            patient_id=test_patient.id,
            provider_id=provider.id,
            start_time=start_time,
            end_time=end_time,
            appointment_type="exam"
        )

        appointment1 = await appointment_service.create_appointment(
            appointment_data=appointment_data1,
            user=test_user
        )

        assert appointment1 is not None

        # Try to create overlapping appointment
        overlapping_start = start_time + timedelta(minutes=30)
        overlapping_end = overlapping_start + timedelta(hours=1)

        appointment_data2 = AppointmentCreate(
            patient_id=test_patient.id,
            provider_id=provider.id,
            start_time=overlapping_start,
            end_time=overlapping_end,
            appointment_type="exam"
        )

        with pytest.raises(HTTPException) as exc_info:
            await appointment_service.create_appointment(
                appointment_data=appointment_data2,
                user=test_user
            )

        assert exc_info.value.status_code == 409
        assert "conflict" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_update_appointment_status(
        self,
        appointment_service: AppointmentService,
        test_patient: Patient,
        test_user: User,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test updating appointment status"""
        from app.core.security import get_password_hash
        
        # Create a unique provider
        provider = User(
            id=uuid4(),
            practice_id=test_practice.id,
            email=f"provider_{uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("secret"),
            role="dentist",
            first_name="Dr.",
            last_name="Smith",
            is_active=True,
            mfa_enabled=True,
            mfa_verified=True
        )
        db_session.add(provider)
        await db_session.commit()
        await db_session.refresh(provider)

        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        # Create appointment
        appointment_data = AppointmentCreate(
            patient_id=test_patient.id,
            provider_id=provider.id,
            start_time=start_time,
            end_time=end_time,
            appointment_type="exam"
        )

        appointment = await appointment_service.create_appointment(
            appointment_data=appointment_data,
            user=test_user
        )

        # Update status
        update_data = AppointmentUpdate(status="confirmed")
        
        updated = await appointment_service.update_appointment(
            appointment_id=appointment.id,
            appointment_data=update_data,
            user=test_user
        )

        assert updated is not None
        assert updated.status == "confirmed"

    @pytest.mark.asyncio
    async def test_cancel_appointment(
        self,
        appointment_service: AppointmentService,
        test_patient: Patient,
        test_user: User,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test canceling an appointment"""
        from app.core.security import get_password_hash
        
        # Create a unique provider
        provider = User(
            id=uuid4(),
            practice_id=test_practice.id,
            email=f"provider_{uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("secret"),
            role="dentist",
            first_name="Dr.",
            last_name="Smith",
            is_active=True,
            mfa_enabled=True,
            mfa_verified=True
        )
        db_session.add(provider)
        await db_session.commit()
        await db_session.refresh(provider)

        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        # Create appointment
        appointment_data = AppointmentCreate(
            patient_id=test_patient.id,
            provider_id=provider.id,
            start_time=start_time,
            end_time=end_time,
            appointment_type="exam"
        )

        appointment = await appointment_service.create_appointment(
            appointment_data=appointment_data,
            user=test_user
        )

        # Cancel appointment
        cancelled = await appointment_service.cancel_appointment(
            appointment_id=appointment.id,
            reason="Patient requested",
            user=test_user
        )

        assert cancelled is not None
        assert cancelled.status == "cancelled"
        assert cancelled.cancellation_reason == "Patient requested"

    @pytest.mark.asyncio
    async def test_get_provider_schedule(
        self,
        appointment_service: AppointmentService,
        test_patient: Patient,
        test_user: User,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test getting provider schedule"""
        from app.core.security import get_password_hash
        
        # Create a unique provider
        provider = User(
            id=uuid4(),
            practice_id=test_practice.id,
            email=f"provider_{uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("secret"),
            role="dentist",
            first_name="Dr.",
            last_name="Smith",
            is_active=True,
            mfa_enabled=True,
            mfa_verified=True
        )
        db_session.add(provider)
        await db_session.commit()
        await db_session.refresh(provider)

        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)

        # Create some appointments
        for i in range(3):
            start_time = start_date + timedelta(days=i, hours=9)
            end_time = start_time + timedelta(hours=1)

            appointment_data = AppointmentCreate(
                patient_id=test_patient.id,
                provider_id=provider.id,
                start_time=start_time,
                end_time=end_time,
                appointment_type="exam"
            )

            await appointment_service.create_appointment(
                appointment_data=appointment_data,
                user=test_user
            )

        # Get provider schedule
        schedule = await appointment_service.get_provider_schedule(
            provider_id=provider.id,
            start_date=start_date,
            end_date=end_date
        )

        assert schedule is not None
        assert len(schedule) >= 3

    @pytest.mark.asyncio
    async def test_appointment_invalid_time_range(
        self,
        appointment_service: AppointmentService,
        test_patient: Patient,
        test_user: User,
        test_practice: Practice,
        db_session: AsyncSession
    ):
        """Test that appointments with invalid time ranges are rejected"""
        from app.core.security import get_password_hash
        from fastapi import HTTPException
        
        # Create a unique provider
        provider = User(
            id=uuid4(),
            practice_id=test_practice.id,
            email=f"provider_{uuid4().hex[:8]}@example.com",
            password_hash=get_password_hash("secret"),
            role="dentist",
            first_name="Dr.",
            last_name="Smith",
            is_active=True,
            mfa_enabled=True,
            mfa_verified=True
        )
        db_session.add(provider)
        await db_session.commit()
        await db_session.refresh(provider)

        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time - timedelta(hours=1)  # End before start!

        appointment_data = AppointmentCreate(
            patient_id=test_patient.id,
            provider_id=provider.id,
            start_time=start_time,
            end_time=end_time,
            appointment_type="exam"
        )

        with pytest.raises(HTTPException) as exc_info:
            await appointment_service.create_appointment(
                appointment_data=appointment_data,
                user=test_user
            )

        assert exc_info.value.status_code == 400
        assert "after" in str(exc_info.value.detail).lower()
