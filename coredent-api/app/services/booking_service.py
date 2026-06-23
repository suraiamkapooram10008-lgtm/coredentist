"""
Booking Service
Core business logic for booking operations
"""

from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import secrets
import string

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.booking import BookingPage, OnlineBooking, WaitlistEntry as Waitlist

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
        page_title: str,
        welcome_message: Optional[str] = None,
        status: Any = None,
    ) -> BookingPage:
        """Create a new booking page"""
        from app.models.booking import BookingPageStatus
        if status is None:
            status = BookingPageStatus.ACTIVE
        booking_page = BookingPage(
            practice_id=practice_id,
            page_title=page_title,
            welcome_message=welcome_message,
            status=status,
            page_slug=page_title.lower().replace(" ", "-"),
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
        page_slug: str,
    ) -> Optional[BookingPage]:
        """Get a public booking page by slug"""
        from app.models.booking import BookingPageStatus
        result = await db.execute(
            select(BookingPage).where(
                BookingPage.page_slug == page_slug,
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

        for key, value in kwargs.items():
            if hasattr(page, key):
                setattr(page, key, value)

        await db.commit()
        await db.refresh(page)
        logger.info(f"Updated booking page: {page_id}")
        return page

    @staticmethod
    async def create_online_booking(
        db: AsyncSession,
        booking_page_id: UUID,
        practice_id: UUID,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        requested_date: date,
        requested_time: Any,
        reason: Optional[str] = None,
    ) -> OnlineBooking:
        """Create a new online booking"""
        from app.models.booking import BookingStatus
        confirmation_code = BookingService.generate_confirmation_code()
        verification_token = BookingService.generate_verification_token()

        booking = OnlineBooking(
            booking_page_id=booking_page_id,
            practice_id=practice_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            requested_date=requested_date,
            requested_time=requested_time,
            reason=reason,
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

        for key, value in kwargs.items():
            if hasattr(booking, key):
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

        from app.models.booking import BookingStatus
        booking.status = BookingStatus.CONFIRMED
        booking.confirmed_at = datetime.now(timezone.utc)

        await db.commit()
        logger.info(f"Confirmed booking: {booking_id}")
        return True

    @staticmethod
    async def add_to_waitlist(
        db: AsyncSession,
        booking_page_id: UUID,
        practice_id: UUID,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        preferred_dates: Optional[List] = None,
        reason: Optional[str] = None,
    ) -> Waitlist:
        """Add a patient to the waitlist"""
        from app.models.booking import WaitlistStatus
        waitlist_entry = Waitlist(
            booking_page_id=booking_page_id,
            practice_id=practice_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            preferred_dates=preferred_dates or [],
            reason=reason,
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
        from app.models.booking import BookingStatus, WaitlistStatus
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
