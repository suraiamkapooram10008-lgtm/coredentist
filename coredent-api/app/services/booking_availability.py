"""
Booking Availability Service
Availability checking and slot management for bookings
"""

from datetime import datetime, timedelta, timezone, time
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.booking import BookingPage, OnlineBooking
from app.models.appointment import Appointment
from app.models.user import User

logger = logging.getLogger(__name__)


class BookingAvailabilityService:
    """Service for booking availability management"""
    
    @staticmethod
    async def get_available_slots(
        db: AsyncSession,
        booking_page_id: UUID,
        date: datetime,
        slot_duration_minutes: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get available time slots for a specific date"""
        # Get booking page to check hours
        result = await db.execute(
            select(BookingPage).where(BookingPage.id == booking_page_id)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            logger.warning(f"Booking page not found: {booking_page_id}")
            return []
        
        # Check if date is a business day
        day_name = date.strftime("%A").lower()
        if page.booking_days:
            allowed_days = page.booking_days.lower().split(",")
            if day_name not in allowed_days:
                logger.info(f"Date {date} is not a business day")
                return []
        
        # Get booking hours
        start_time = page.booking_start_time or time(9, 0)
        end_time = page.booking_end_time or time(17, 0)
        
        # Generate all possible slots
        slots = []
        current_time = datetime.combine(date.date(), start_time)
        end_datetime = datetime.combine(date.date(), end_time)
        
        while current_time < end_datetime:
            slot_end = current_time + timedelta(minutes=slot_duration_minutes)
            
            # Check if slot is available
            is_available = await BookingAvailabilityService._is_slot_available(
                db, booking_page_id, current_time, slot_end
            )
            
            if is_available:
                slots.append({
                    "start_time": current_time.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "available": True,
                })
            
            current_time = slot_end
        
        logger.info(f"Found {len(slots)} available slots for {date}")
        return slots
    
    @staticmethod
    async def _is_slot_available(
        db: AsyncSession,
        booking_page_id: UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """Check if a time slot is available"""
        # Check for conflicting bookings
        result = await db.execute(
            select(func.count(OnlineBooking.id)).where(
                OnlineBooking.booking_page_id == booking_page_id,
                OnlineBooking.appointment_date >= start_time,
                OnlineBooking.appointment_date < end_time,
                OnlineBooking.status.in_(["pending", "confirmed"]),
            )
        )
        booking_count = result.scalar() or 0
        
        # Allow up to 3 bookings per slot
        if booking_count >= 3:
            return False
        
        return True
    
    @staticmethod
    async def get_available_dates(
        db: AsyncSession,
        booking_page_id: UUID,
        days_ahead: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get available dates for booking"""
        result = await db.execute(
            select(BookingPage).where(BookingPage.id == booking_page_id)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            return []
        
        available_dates = []
        now = datetime.now(timezone.utc)
        
        for i in range(1, days_ahead + 1):
            check_date = now + timedelta(days=i)
            day_name = check_date.strftime("%A").lower()
            
            # Check if it's a business day
            if page.booking_days:
                allowed_days = page.booking_days.lower().split(",")
                if day_name not in allowed_days:
                    continue
            
            # Check if there are available slots
            slots = await BookingAvailabilityService.get_available_slots(
                db, booking_page_id, check_date
            )
            
            if slots:
                available_dates.append({
                    "date": check_date.date().isoformat(),
                    "day_name": day_name,
                    "available_slots": len(slots),
                })
        
        return available_dates
    
    @staticmethod
    async def get_provider_availability(
        db: AsyncSession,
        provider_id: UUID,
        date: datetime,
    ) -> List[Dict[str, Any]]:
        """Get availability for a specific provider"""
        # Get provider's appointments for the date
        result = await db.execute(
            select(Appointment).where(
                Appointment.provider_id == provider_id,
                Appointment.start_time >= date.replace(hour=0, minute=0, second=0),
                Appointment.start_time < date.replace(hour=23, minute=59, second=59),
            )
        )
        appointments = result.scalars().all()
        
        # Calculate available slots (assuming 30-min slots, 9am-5pm)
        available_slots = []
        start_time = datetime.combine(date.date(), time(9, 0))
        end_time = datetime.combine(date.date(), time(17, 0))
        
        current_time = start_time
        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=30)
            
            # Check if slot conflicts with any appointment
            is_free = True
            for appt in appointments:
                if (current_time < appt.end_time and slot_end > appt.start_time):
                    is_free = False
                    break
            
            if is_free:
                available_slots.append({
                    "start_time": current_time.isoformat(),
                    "end_time": slot_end.isoformat(),
                })
            
            current_time = slot_end
        
        return available_slots
    
    @staticmethod
    def calculate_slot_duration(
        appointment_type: str,
        default_duration: int = 30,
    ) -> int:
        """Calculate slot duration based on appointment type"""
        # Map appointment types to durations
        duration_map = {
            "checkup": 30,
            "cleaning": 45,
            "filling": 60,
            "root_canal": 90,
            "extraction": 45,
            "consultation": 30,
            "follow_up": 20,
        }
        
        return duration_map.get(appointment_type.lower(), default_duration)
    
    @staticmethod
    async def check_room_availability(
        db: AsyncSession,
        practice_id: UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_appointment_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a room is available for the time slot"""
        query = select(func.count(Appointment.id)).where(
            Appointment.practice_id == practice_id,
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
            Appointment.status.in_(["scheduled", "in_progress"]),
        )
        
        if exclude_appointment_id:
            query = query.where(Appointment.id != exclude_appointment_id)
        
        result = await db.execute(query)
        conflicting_count = result.scalar() or 0
        
        # Assuming we have multiple rooms, allow up to 3 concurrent appointments
        return conflicting_count < 3
    
    @staticmethod
    async def get_booking_statistics(
        db: AsyncSession,
        booking_page_id: UUID,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get booking statistics"""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)
        
        # Total bookings in period
        total_result = await db.execute(
            select(func.count(OnlineBooking.id)).where(
                OnlineBooking.booking_page_id == booking_page_id,
                OnlineBooking.created_at >= start_date,
            )
        )
        total_bookings = total_result.scalar() or 0
        
        # Confirmed bookings
        confirmed_result = await db.execute(
            select(func.count(OnlineBooking.id)).where(
                OnlineBooking.booking_page_id == booking_page_id,
                OnlineBooking.status == "confirmed",
                OnlineBooking.created_at >= start_date,
            )
        )
        confirmed_bookings = confirmed_result.scalar() or 0
        
        # Cancelled bookings
        cancelled_result = await db.execute(
            select(func.count(OnlineBooking.id)).where(
                OnlineBooking.booking_page_id == booking_page_id,
                OnlineBooking.status == "cancelled",
                OnlineBooking.created_at >= start_date,
            )
        )
        cancelled_bookings = cancelled_result.scalar() or 0
        
        # Average bookings per day
        avg_per_day = total_bookings / max(days, 1)
        
        return {
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "cancelled_bookings": cancelled_bookings,
            "pending_bookings": total_bookings - confirmed_bookings - cancelled_bookings,
            "confirmation_rate": (confirmed_bookings / max(total_bookings, 1)) * 100,
            "cancellation_rate": (cancelled_bookings / max(total_bookings, 1)) * 100,
            "average_per_day": round(avg_per_day, 2),
        }
