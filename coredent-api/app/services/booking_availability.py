"""
Booking Availability Service
Manages time slot availability for bookings
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class BookingAvailabilityService:
    """Service for managing booking availability"""

    @staticmethod
    async def get_available_slots(
        db: AsyncSession,
        practice_id: str,
        date: Optional[datetime] = None,
        duration_minutes: int = 60,
    ) -> List[dict]:
        """Get available time slots for a given date and practice"""
        from app.models.booking import BookingAvailability

        if date is None:
            date = datetime.now(timezone.utc)

        query = select(BookingAvailability).where(
            BookingAvailability.practice_id == practice_id,
            BookingAvailability.is_available == True,
        )
        result = await db.execute(query)
        slots = result.scalars().all()
        return [
            {
                "start_time": slot.start_time.isoformat() if hasattr(slot.start_time, 'isoformat') else str(slot.start_time),
                "end_time": slot.end_time.isoformat() if hasattr(slot.end_time, 'isoformat') else str(slot.end_time),
                "is_available": slot.is_available,
            }
            for slot in slots
        ]

    @staticmethod
    async def is_slot_available(
        db: AsyncSession,
        practice_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """Check if a specific time slot is available"""
        from app.models.booking import BookingAvailability

        query = select(BookingAvailability).where(
            BookingAvailability.practice_id == practice_id,
            BookingAvailability.start_time <= start_time,
            BookingAvailability.end_time >= end_time,
            BookingAvailability.is_available == True,
        )
        result = await db.execute(query)
        slot = result.scalar_one_or_none()
        return slot is not None