"""
Appointment Service - Business Logic
Handles appointment scheduling, slot management, and status transitions
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


class AppointmentService:
    """Service for managing appointments"""

    @staticmethod
    def create_appointment(
        db: Session,
        appointment_data: AppointmentCreate,
        practice_id: int,
        created_by_id: int
    ) -> Appointment:
        """Create a new appointment with validation"""
        
        # Validate slot availability
        if not AppointmentService.is_slot_available(
            db=db,
            provider_id=appointment_data.provider_id,
            start_time=appointment_data.start_time,
            end_time=appointment_data.end_time,
            practice_id=practice_id
        ):
            raise ValueError("Time slot is not available")
        
        # Create appointment — exclude status from model_dump to avoid conflict
        data = appointment_data.model_dump(exclude={'status'})
        appointment = Appointment(
            **data,
            practice_id=practice_id,
            created_by_id=created_by_id,
            status=AppointmentStatus.SCHEDULED
        )
        
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        
        return appointment

    @staticmethod
    def is_slot_available(
        db: Session,
        provider_id: int,
        start_time: datetime,
        end_time: datetime,
        practice_id: int,
        exclude_appointment_id: Optional[int] = None
    ) -> bool:
        """Check if a time slot is available for a provider"""
        
        query = db.query(Appointment).filter(
            and_(
                Appointment.provider_id == provider_id,
                Appointment.practice_id == practice_id,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.IN_PROGRESS
                ]),
                or_(
                    # New appointment starts during existing appointment
                    and_(
                        Appointment.start_time <= start_time,
                        Appointment.end_time > start_time
                    ),
                    # New appointment ends during existing appointment
                    and_(
                        Appointment.start_time < end_time,
                        Appointment.end_time >= end_time
                    ),
                    # New appointment completely contains existing appointment
                    and_(
                        Appointment.start_time >= start_time,
                        Appointment.end_time <= end_time
                    )
                )
            )
        )
        
        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)
        
        conflicting_appointments = query.count()
        return conflicting_appointments == 0

    @staticmethod
    def get_available_slots(
        db: Session,
        provider_id: int,
        date: datetime,
        practice_id: int,
        duration_minutes: int = 30,
        start_hour: int = 9,
        end_hour: int = 17
    ) -> List[Dict[str, Any]]:
        """Get available time slots for a provider on a specific date"""
        
        # Get all appointments for the provider on this date
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        appointments = db.query(Appointment).filter(
            and_(
                Appointment.provider_id == provider_id,
                Appointment.practice_id == practice_id,
                Appointment.start_time >= start_of_day,
                Appointment.start_time < end_of_day,
                Appointment.status.in_([
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.IN_PROGRESS
                ])
            )
        ).order_by(Appointment.start_time).all()
        
        # Generate all possible slots
        available_slots = []
        current_time = start_of_day.replace(hour=start_hour, minute=0)
        end_time = start_of_day.replace(hour=end_hour, minute=0)
        
        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            # Check if slot conflicts with any appointment
            is_available = True
            for appointment in appointments:
                if (current_time < appointment.end_time and 
                    slot_end > appointment.start_time):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    "start_time": current_time,
                    "end_time": slot_end,
                    "duration_minutes": duration_minutes
                })
            
            current_time = slot_end
        
        return available_slots

    @staticmethod
    def update_appointment_status(
        db: Session,
        appointment_id: int,
        new_status: AppointmentStatus,
        practice_id: int,
        updated_by_id: int,
        notes: Optional[str] = None
    ) -> Appointment:
        """Update appointment status with validation"""
        
        appointment = db.query(Appointment).filter(
            and_(
                Appointment.id == appointment_id,
                Appointment.practice_id == practice_id
            )
        ).first()
        
        if not appointment:
            raise ValueError("Appointment not found")
        
        # Validate status transition
        valid_transitions = {
            AppointmentStatus.SCHEDULED: [
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.CANCELLED,
                AppointmentStatus.NO_SHOW
            ],
            AppointmentStatus.CONFIRMED: [
                AppointmentStatus.IN_PROGRESS,
                AppointmentStatus.CANCELLED,
                AppointmentStatus.NO_SHOW
            ],
            AppointmentStatus.IN_PROGRESS: [
                AppointmentStatus.COMPLETED,
                AppointmentStatus.CANCELLED
            ],
            AppointmentStatus.COMPLETED: [],
            AppointmentStatus.CANCELLED: [],
            AppointmentStatus.NO_SHOW: []
        }
        
        if new_status not in valid_transitions.get(appointment.status, []):
            raise ValueError(
                f"Invalid status transition from {appointment.status} to {new_status}"
            )
        
        appointment.status = new_status
        appointment.updated_at = datetime.now(timezone.utc)
        
        if notes:
            appointment.notes = notes
        
        db.commit()
        db.refresh(appointment)
        
        return appointment

    @staticmethod
    def cancel_appointment(
        db: Session,
        appointment_id: int,
        practice_id: int,
        cancelled_by_id: int,
        cancellation_reason: Optional[str] = None
    ) -> Appointment:
        """Cancel an appointment"""
        
        return AppointmentService.update_appointment_status(
            db=db,
            appointment_id=appointment_id,
            new_status=AppointmentStatus.CANCELLED,
            practice_id=practice_id,
            updated_by_id=cancelled_by_id,
            notes=cancellation_reason
        )

    @staticmethod
    def complete_appointment(
        db: Session,
        appointment_id: int,
        practice_id: int,
        completed_by_id: int,
        completion_notes: Optional[str] = None
    ) -> Appointment:
        """Mark appointment as completed"""
        
        return AppointmentService.update_appointment_status(
            db=db,
            appointment_id=appointment_id,
            new_status=AppointmentStatus.COMPLETED,
            practice_id=practice_id,
            updated_by_id=completed_by_id,
            notes=completion_notes
        )

    @staticmethod
    def get_appointments_by_date_range(
        db: Session,
        practice_id: int,
        start_date: datetime,
        end_date: datetime,
        provider_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """Get appointments within a date range with optional filters"""
        
        query = db.query(Appointment).filter(
            and_(
                Appointment.practice_id == practice_id,
                Appointment.start_time >= start_date,
                Appointment.start_time < end_date
            )
        )
        
        if provider_id:
            query = query.filter(Appointment.provider_id == provider_id)
        
        if patient_id:
            query = query.filter(Appointment.patient_id == patient_id)
        
        if status:
            query = query.filter(Appointment.status == status)
        
        return query.order_by(Appointment.start_time).all()

    @staticmethod
    def get_provider_schedule(
        db: Session,
        provider_id: int,
        date: datetime,
        practice_id: int
    ) -> Dict[str, Any]:
        """Get provider's schedule for a specific date"""
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        appointments = AppointmentService.get_appointments_by_date_range(
            db=db,
            practice_id=practice_id,
            start_date=start_of_day,
            end_date=end_of_day,
            provider_id=provider_id
        )
        
        available_slots = AppointmentService.get_available_slots(
            db=db,
            provider_id=provider_id,
            date=date,
            practice_id=practice_id
        )
        
        return {
            "date": date.date(),
            "provider_id": provider_id,
            "appointments": appointments,
            "available_slots": available_slots,
            "total_appointments": len(appointments),
            "total_available_slots": len(available_slots)
        }
