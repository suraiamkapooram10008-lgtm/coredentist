"""
Booking Validation Service
Validation logic for booking operations
"""

from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import UUID
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.booking import BookingPage, OnlineBooking
from app.models.appointment import Appointment
from app.models.patient import Patient

logger = logging.getLogger(__name__)


class BookingValidationService:
    """Service for booking validation"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
        # Check if it's at least 10 digits
        return len(cleaned) >= 10 and cleaned.isdigit()
    
    @staticmethod
    def validate_booking_data(
        patient_name: str,
        patient_email: str,
        patient_phone: str,
        appointment_date: datetime,
    ) -> Tuple[bool, Optional[str]]:
        """Validate booking data"""
        # Validate patient name
        if not patient_name or len(patient_name.strip()) < 2:
            return False, "Patient name must be at least 2 characters"
        
        # Validate email
        if not BookingValidationService.validate_email(patient_email):
            return False, "Invalid email format"
        
        # Validate phone
        if not BookingValidationService.validate_phone(patient_phone):
            return False, "Invalid phone number format"
        
        # Validate appointment date
        now = datetime.now(timezone.utc)
        if appointment_date <= now:
            return False, "Appointment date must be in the future"
        
        # Check if appointment is not too far in the future (e.g., more than 1 year)
        max_future = now.replace(year=now.year + 1)
        if appointment_date > max_future:
            return False, "Appointment date cannot be more than 1 year in the future"
        
        return True, None
    
    @staticmethod
    async def check_booking_conflicts(
        db: AsyncSession,
        booking_page_id: UUID,
        appointment_date: datetime,
        appointment_type: str,
        exclude_booking_id: Optional[UUID] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Check for booking conflicts"""
        # Check if there are too many bookings at the same time
        time_window = 30  # minutes
        start_time = appointment_date.replace(minute=0, second=0, microsecond=0)
        end_time = start_time.replace(minute=time_window)
        
        query = select(OnlineBooking).where(
            OnlineBooking.booking_page_id == booking_page_id,
            OnlineBooking.appointment_date >= start_time,
            OnlineBooking.appointment_date <= end_time,
            OnlineBooking.status.in_(["pending", "confirmed"]),
        )
        
        if exclude_booking_id:
            query = query.where(OnlineBooking.id != exclude_booking_id)
        
        result = await db.execute(query)
        conflicting_bookings = result.scalars().all()
        
        # Allow up to 3 bookings in the same time window
        if len(conflicting_bookings) >= 3:
            return False, "This time slot is fully booked. Please choose another time."
        
        return True, None
    
    @staticmethod
    async def validate_patient_exists(
        db: AsyncSession,
        patient_email: str,
        patient_phone: str,
    ) -> Optional[Patient]:
        """Check if patient already exists"""
        result = await db.execute(
            select(Patient).where(
                Patient.email == patient_email
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def validate_booking_page(
        db: AsyncSession,
        page_id: UUID,
    ) -> Tuple[bool, Optional[str]]:
        """Validate booking page exists and is active"""
        result = await db.execute(
            select(BookingPage).where(BookingPage.id == page_id)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            return False, "Booking page not found"
        
        if not page.is_active:
            return False, "Booking page is not active"
        
        return True, None
    
    @staticmethod
    async def validate_appointment_type(
        db: AsyncSession,
        booking_page_id: UUID,
        appointment_type: str,
    ) -> Tuple[bool, Optional[str]]:
        """Validate appointment type is available"""
        result = await db.execute(
            select(BookingPage).where(BookingPage.id == booking_page_id)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            return False, "Booking page not found"
        
        # Check if appointment type is in the allowed types
        if page.allowed_appointment_types:
            allowed_types = page.allowed_appointment_types.split(",")
            if appointment_type not in allowed_types:
                return False, f"Appointment type '{appointment_type}' is not available"
        
        return True, None
    
    @staticmethod
    async def validate_booking_hours(
        db: AsyncSession,
        booking_page_id: UUID,
        appointment_date: datetime,
    ) -> Tuple[bool, Optional[str]]:
        """Validate appointment is within booking hours"""
        result = await db.execute(
            select(BookingPage).where(BookingPage.id == booking_page_id)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            return False, "Booking page not found"
        
        # Check if appointment is on a business day
        if page.booking_days:
            day_name = appointment_date.strftime("%A").lower()
            allowed_days = page.booking_days.lower().split(",")
            if day_name not in allowed_days:
                return False, f"Bookings are not available on {day_name}s"
        
        # Check if appointment is within booking hours
        if page.booking_start_time and page.booking_end_time:
            appointment_time = appointment_date.time()
            if not (page.booking_start_time <= appointment_time <= page.booking_end_time):
                return False, "Appointment time is outside booking hours"
        
        return True, None
    
    @staticmethod
    async def validate_complete_booking(
        db: AsyncSession,
        booking_page_id: UUID,
        patient_name: str,
        patient_email: str,
        patient_phone: str,
        appointment_date: datetime,
        appointment_type: str,
    ) -> Tuple[bool, Optional[str]]:
        """Perform complete booking validation"""
        # Validate basic data
        is_valid, error = BookingValidationService.validate_booking_data(
            patient_name, patient_email, patient_phone, appointment_date
        )
        if not is_valid:
            return False, error
        
        # Validate booking page
        is_valid, error = await BookingValidationService.validate_booking_page(
            db, booking_page_id
        )
        if not is_valid:
            return False, error
        
        # Validate appointment type
        is_valid, error = await BookingValidationService.validate_appointment_type(
            db, booking_page_id, appointment_type
        )
        if not is_valid:
            return False, error
        
        # Validate booking hours
        is_valid, error = await BookingValidationService.validate_booking_hours(
            db, booking_page_id, appointment_date
        )
        if not is_valid:
            return False, error
        
        # Check for conflicts
        is_valid, error = await BookingValidationService.check_booking_conflicts(
            db, booking_page_id, appointment_date, appointment_type
        )
        if not is_valid:
            return False, error
        
        return True, None
