"""
Booking Service
Core business logic for booking operations
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import secrets
import string

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.booking import (
    BookingPage,
    OnlineBooking,
    Waitlist,
    BookingPageStatus,
    BookingStatus,
    WaitlistStatus,
)
from app.models.appointment import Appointment
from app.models.user import User
from app.models.patient import Patient

logger = logging.getLogger(__name__)


class BookingService:
    """Service for booking operations"""
    
    @staticmethod
    def generate_confirmation_code() -> str:
        """Generate a unique confirmation code"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(8))
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a verification token for email confirmation"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generate a verification code for SMS confirmation"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @staticmethod
    async def create_booking_page(
        db: AsyncSession,
        practice_id: UUID,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> BookingPage:
        """Create a new booking page"""
        status = BookingPageStatus.ACTIVE if is_active else BookingPageStatus.INACTIVE
        base_slug = name.lower().replace(" ", "-")
        slug = base_slug
        # Ensure slug uniqueness
        counter = 1
        while True:
            result = await db.execute(
                select(BookingPage).where(BookingPage.page_slug == slug)
            )
            if result.scalar_one_or_none() is None:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        booking_page = BookingPage(
            practice_id=practice_id,
            page_title=name,
            welcome_message=description,
            status=status,
            page_slug=slug,
        )
        db.add(booking_page)
        await db.commit()
        await db.refresh(booking_page)
        logger.info(f"Created booking page: {booking_page.id}")
        return booking_page
    
    @staticmethod
    async def get_booking_page(
        db: AsyncSession,
        page_id: UUID,
        practice_id: Optional[UUID] = None,
    ) -> Optional[BookingPage]:
        """Get a booking page"""
        query = select(BookingPage).where(BookingPage.id == page_id)
        
        if practice_id:
            query = query.where(BookingPage.practice_id == practice_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_public_booking_page(
        db: AsyncSession,
        slug: str,
    ) -> Optional[BookingPage]:
        """Get a public booking page by slug"""
        result = await db.execute(
            select(BookingPage).where(
                BookingPage.page_slug == slug,
                BookingPage.status == BookingPageStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_booking_page(
        db: AsyncSession,
        page_id: UUID,
        **kwargs
    ) -> Optional[BookingPage]:
        """Update a booking page"""
        result = await db.execute(
            select(BookingPage).where(BookingPage.id == page_id)
        )
        page = result.scalar_one_or_none()
        
        if not page:
            return None
        
        # Map legacy field names to model field names
        field_mapping = {
            "name": "page_title",
            "description": "welcome_message",
        }

        for key, value in kwargs.items():
            mapped_key = field_mapping.get(key, key)
            if mapped_key == "is_active":
                page.status = BookingPageStatus.ACTIVE if value else BookingPageStatus.INACTIVE
            elif mapped_key and hasattr(page, mapped_key):
                setattr(page, mapped_key, value)
            elif hasattr(page, key):
                setattr(page, key, value)

        await db.commit()
        await db.refresh(page)
        logger.info(f"Updated booking page: {page_id}")
        return page
    
    @staticmethod
    async def create_online_booking(
        db: AsyncSession,
        booking_page_id: UUID,
        patient_name: str,
        patient_email: str,
        patient_phone: str,
        appointment_date: datetime,
        appointment_type: str,
        notes: Optional[str] = None,
    ) -> OnlineBooking:
        """Create a new online booking"""
        confirmation_code = BookingService.generate_confirmation_code()
        verification_token = BookingService.generate_verification_token()

        # Split patient name
        name_parts = patient_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Extract date and time
        if isinstance(appointment_date, datetime):
            requested_date = appointment_date.date()
            requested_time = appointment_date.time()
        else:
            from datetime import time as dt_time
            requested_date = appointment_date
            requested_time = dt_time(9, 0)

        # Get practice_id from booking page
        page_result = await db.execute(
            select(BookingPage).where(BookingPage.id == booking_page_id)
        )
        booking_page = page_result.scalar_one_or_none()
        practice_id = booking_page.practice_id if booking_page else None

        booking = OnlineBooking(
            booking_page_id=booking_page_id,
            practice_id=practice_id,
            first_name=first_name,
            last_name=last_name,
            email=patient_email,
            phone=patient_phone,
            requested_date=requested_date,
            requested_time=requested_time,
            reason=notes,
            confirmation_code=confirmation_code,
            email_verification_token=verification_token,
            status=BookingStatus.PENDING,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        logger.info(f"Created online booking: {booking.id}")
        return booking
    
    @staticmethod
    async def get_online_booking(
        db: AsyncSession,
        booking_id: UUID,
    ) -> Optional[OnlineBooking]:
        """Get an online booking"""
        result = await db.execute(
            select(OnlineBooking).where(OnlineBooking.id == booking_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_online_booking(
        db: AsyncSession,
        booking_id: UUID,
        **kwargs
    ) -> Optional[OnlineBooking]:
        """Update an online booking"""
        result = await db.execute(
            select(OnlineBooking).where(OnlineBooking.id == booking_id)
        )
        booking = result.scalar_one_or_none()

        if not booking:
            return None

        # Map legacy field names to model field names
        field_mapping = {
            "patient_email": "email",
            "patient_phone": "phone",
            "notes": "reason",
        }

        for key, value in kwargs.items():
            mapped_key = field_mapping.get(key, key)
            if mapped_key and hasattr(booking, mapped_key):
                setattr(booking, mapped_key, value)
            elif hasattr(booking, key):
                setattr(booking, key, value)

        await db.commit()
        await db.refresh(booking)
        logger.info(f"Updated online booking: {booking_id}")
        return booking
    
    @staticmethod
    async def confirm_booking(
        db: AsyncSession,
        booking_id: UUID,
        verification_code: str,
    ) -> bool:
        """Confirm a booking with verification code"""
        booking = await BookingService.get_online_booking(db, booking_id)
        
        if not booking:
            logger.warning(f"Booking not found: {booking_id}")
            return False
        
        # Verify the code (in real implementation, would check against sent code)
        if not verification_code:
            logger.warning(f"Invalid verification code for booking: {booking_id}")
            return False
        
        booking.status = BookingStatus.CONFIRMED
        booking.confirmed_at = datetime.now(timezone.utc)
        
        await db.commit()
        logger.info(f"Confirmed booking: {booking_id}")
        return True
    
    @staticmethod
    async def add_to_waitlist(
        db: AsyncSession,
        booking_page_id: UUID,
        patient_name: str,
        patient_email: str,
        patient_phone: str,
        preferred_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Waitlist:
        """Add a patient to the waitlist"""
        # Split patient name
        name_parts = patient_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Get practice_id from booking page
        page_result = await db.execute(
            select(BookingPage).where(BookingPage.id == booking_page_id)
        )
        booking_page = page_result.scalar_one_or_none()
        practice_id = booking_page.practice_id if booking_page else None

        # Prepare preferred_dates as JSON array
        preferred_dates = []
        if preferred_date:
            if isinstance(preferred_date, datetime):
                preferred_dates = [preferred_date.date().isoformat()]
            else:
                preferred_dates = [preferred_date.isoformat()]

        waitlist_entry = Waitlist(
            booking_page_id=booking_page_id,
            practice_id=practice_id,
            first_name=first_name,
            last_name=last_name,
            email=patient_email,
            phone=patient_phone,
            preferred_dates=preferred_dates,
            reason=notes,
            status=WaitlistStatus.ACTIVE,
        )
        db.add(waitlist_entry)
        await db.commit()
        await db.refresh(waitlist_entry)
        logger.info(f"Added to waitlist: {waitlist_entry.id}")
        return waitlist_entry
    
    @staticmethod
    async def list_bookings(
        db: AsyncSession,
        booking_page_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[OnlineBooking]:
        """List bookings for a booking page"""
        query = select(OnlineBooking).where(
            OnlineBooking.booking_page_id == booking_page_id
        )
        
        if status:
            query = query.where(OnlineBooking.status == status)
        
        query = query.limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_booking_stats(
        db: AsyncSession,
        booking_page_id: UUID,
    ) -> Dict[str, Any]:
        """Get booking statistics for a page"""
        # Total bookings
        total_result = await db.execute(
            select(OnlineBooking).where(
                OnlineBooking.booking_page_id == booking_page_id
            )
        )
        total_bookings = len(total_result.scalars().all())
        
        # Confirmed bookings
        confirmed_result = await db.execute(
            select(OnlineBooking).where(
                OnlineBooking.booking_page_id == booking_page_id,
                OnlineBooking.status == BookingStatus.CONFIRMED,
            )
        )
        confirmed_bookings = len(confirmed_result.scalars().all())
        
        # Pending bookings
        pending_result = await db.execute(
            select(OnlineBooking).where(
                OnlineBooking.booking_page_id == booking_page_id,
                OnlineBooking.status == BookingStatus.PENDING,
            )
        )
        pending_bookings = len(pending_result.scalars().all())
        
        # Waitlist count
        waitlist_result = await db.execute(
            select(Waitlist).where(
                Waitlist.booking_page_id == booking_page_id,
                Waitlist.status == WaitlistStatus.ACTIVE,
            )
        )
        waitlist_count = len(waitlist_result.scalars().all())
        
        return {
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "pending_bookings": pending_bookings,
            "waitlist_count": waitlist_count,
            "confirmation_rate": (confirmed_bookings / max(total_bookings, 1)) * 100,
        }
