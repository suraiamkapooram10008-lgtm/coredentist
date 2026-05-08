"""
Tests for BookingService
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.booking_service import BookingService
from app.models.booking import (
    BookingPage,
    OnlineBooking,
    Waitlist,
    BookingPageStatus,
    BookingStatus,
    WaitlistStatus,
)
from app.models.practice import Practice


class TestBookingService:
    """Test suite for BookingService"""

    @pytest.mark.asyncio
    async def test_generate_confirmation_code(self):
        """Test confirmation code generation"""
        code = BookingService.generate_confirmation_code()
        
        assert code is not None
        assert len(code) == 8
        assert code.isalnum()
        assert code.isupper() or code.isdigit()

    @pytest.mark.asyncio
    async def test_generate_verification_token(self):
        """Test verification token generation"""
        token = BookingService.generate_verification_token()
        
        assert token is not None
        assert len(token) > 20  # URL-safe tokens are longer

    @pytest.mark.asyncio
    async def test_generate_verification_code(self):
        """Test verification code generation"""
        code = BookingService.generate_verification_code()
        
        assert code is not None
        assert len(code) == 6
        assert code.isdigit()

    @pytest.mark.asyncio
    async def test_create_booking_page(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test creating a booking page"""
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="General Dentistry",
            description="Book your dental appointment",
            is_active=True
        )

        assert booking_page is not None
        assert booking_page.page_title == "General Dentistry"
        assert booking_page.practice_id == test_practice.id
        assert booking_page.status == BookingPageStatus.ACTIVE
        assert booking_page.page_slug == "general-dentistry"

    @pytest.mark.asyncio
    async def test_get_booking_page(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test getting a booking page"""
        # Create booking page
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="Test Page",
            is_active=True
        )

        # Get booking page
        retrieved = await BookingService.get_booking_page(
            db=db_session,
            page_id=booking_page.id,
            practice_id=test_practice.id
        )

        assert retrieved is not None
        assert retrieved.id == booking_page.id
        assert retrieved.page_title == "Test Page"

    @pytest.mark.asyncio
    async def test_get_public_booking_page(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test getting a public booking page by slug"""
        # Create booking page
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="Public Page",
            is_active=True
        )

        # Get by slug
        retrieved = await BookingService.get_public_booking_page(
            db=db_session,
            slug="public-page"
        )

        assert retrieved is not None
        assert retrieved.id == booking_page.id

    @pytest.mark.asyncio
    async def test_update_booking_page(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test updating a booking page"""
        # Create booking page
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="Original Name",
            is_active=True
        )

        # Update booking page
        updated = await BookingService.update_booking_page(
            db=db_session,
            page_id=booking_page.id,
            name="Updated Name",
            description="New description"
        )

        assert updated is not None
        assert updated.page_title == "Updated Name"
        assert updated.welcome_message == "New description"

    @pytest.mark.asyncio
    async def test_create_online_booking(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test creating an online booking"""
        # Create booking page first
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="Test Page",
            is_active=True
        )

        # Create online booking
        appointment_date = datetime.now() + timedelta(days=7)
        booking = await BookingService.create_online_booking(
            db=db_session,
            booking_page_id=booking_page.id,
            patient_name="John Doe",
            patient_email="john@example.com",
            patient_phone="555-0100",
            appointment_date=appointment_date,
            appointment_type="checkup",
            notes="First visit"
        )

        assert booking is not None
        assert booking.first_name == "John"
        assert booking.last_name == "Doe"
        assert booking.email == "john@example.com"
        assert booking.status == BookingStatus.PENDING
        assert booking.confirmation_code is not None
        assert len(booking.confirmation_code) == 8

    @pytest.mark.asyncio
    async def test_get_online_booking(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test getting an online booking"""
        # Create booking page and booking
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="Test Page",
            is_active=True
        )

        appointment_date = datetime.now() + timedelta(days=7)
        booking = await BookingService.create_online_booking(
            db=db_session,
            booking_page_id=booking_page.id,
            patient_name="Jane Smith",
            patient_email="jane@example.com",
            patient_phone="555-0200",
            appointment_date=appointment_date,
            appointment_type="cleaning"
        )

        # Get booking
        retrieved = await BookingService.get_online_booking(
            db=db_session,
            booking_id=booking.id
        )

        assert retrieved is not None
        assert retrieved.id == booking.id
        assert retrieved.first_name == "Jane"
        assert retrieved.last_name == "Smith"

    @pytest.mark.asyncio
    async def test_update_online_booking(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test updating an online booking"""
        # Create booking
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="Test Page",
            is_active=True
        )

        appointment_date = datetime.now() + timedelta(days=7)
        booking = await BookingService.create_online_booking(
            db=db_session,
            booking_page_id=booking_page.id,
            patient_name="John Doe",
            patient_email="john@example.com",
            patient_phone="555-0100",
            appointment_date=appointment_date,
            appointment_type="checkup"
        )

        # Update booking
        updated = await BookingService.update_online_booking(
            db=db_session,
            booking_id=booking.id,
            status="confirmed",
            notes="Updated notes"
        )

        assert updated is not None
        assert updated.status == BookingStatus.CONFIRMED
        assert updated.reason == "Updated notes"

    @pytest.mark.asyncio
    async def test_confirm_booking(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test confirming a booking"""
        # Create booking
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="Test Page",
            is_active=True
        )

        appointment_date = datetime.now() + timedelta(days=7)
        booking = await BookingService.create_online_booking(
            db=db_session,
            booking_page_id=booking_page.id,
            patient_name="John Doe",
            patient_email="john@example.com",
            patient_phone="555-0100",
            appointment_date=appointment_date,
            appointment_type="checkup"
        )

        # Confirm booking
        confirmed = await BookingService.confirm_booking(
            db=db_session,
            booking_id=booking.id,
            verification_code="123456"
        )

        assert confirmed is True

        # Verify status changed
        updated_booking = await BookingService.get_online_booking(
            db=db_session,
            booking_id=booking.id
        )
        assert updated_booking.status == BookingStatus.CONFIRMED
        assert updated_booking.confirmed_at is not None

    @pytest.mark.asyncio
    async def test_add_to_waitlist(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test adding a patient to waitlist"""
        # Create booking page
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="Test Page",
            is_active=True
        )

        # Add to waitlist
        preferred_date = datetime.now() + timedelta(days=14)
        waitlist_entry = await BookingService.add_to_waitlist(
            db=db_session,
            booking_page_id=booking_page.id,
            patient_name="Bob Wilson",
            patient_email="bob@example.com",
            patient_phone="555-0300",
            preferred_date=preferred_date,
            notes="Flexible schedule"
        )

        assert waitlist_entry is not None
        assert waitlist_entry.first_name == "Bob"
        assert waitlist_entry.last_name == "Wilson"
        assert waitlist_entry.status == WaitlistStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_list_bookings(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test listing bookings for a page"""
        # Create booking page
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="Test Page",
            is_active=True
        )

        # Create multiple bookings
        for i in range(3):
            appointment_date = datetime.now() + timedelta(days=7+i)
            await BookingService.create_online_booking(
                db=db_session,
                booking_page_id=booking_page.id,
                patient_name=f"Patient {i}",
                patient_email=f"patient{i}@example.com",
                patient_phone=f"555-010{i}",
                appointment_date=appointment_date,
                appointment_type="checkup"
            )

        # List bookings
        bookings = await BookingService.list_bookings(
            db=db_session,
            booking_page_id=booking_page.id
        )

        assert len(bookings) >= 3

    @pytest.mark.asyncio
    async def test_get_booking_stats(
        self,
        db_session: AsyncSession,
        test_practice: Practice
    ):
        """Test getting booking statistics"""
        # Create booking page
        booking_page = await BookingService.create_booking_page(
            db=db_session,
            practice_id=test_practice.id,
            name="Test Page",
            is_active=True
        )

        # Create bookings with different statuses
        appointment_date = datetime.now() + timedelta(days=7)
        
        # Pending booking
        await BookingService.create_online_booking(
            db=db_session,
            booking_page_id=booking_page.id,
            patient_name="Patient 1",
            patient_email="patient1@example.com",
            patient_phone="555-0101",
            appointment_date=appointment_date,
            appointment_type="checkup"
        )

        # Confirmed booking
        booking2 = await BookingService.create_online_booking(
            db=db_session,
            booking_page_id=booking_page.id,
            patient_name="Patient 2",
            patient_email="patient2@example.com",
            patient_phone="555-0102",
            appointment_date=appointment_date,
            appointment_type="cleaning"
        )
        await BookingService.update_online_booking(
            db=db_session,
            booking_id=booking2.id,
            status="confirmed"
        )

        # Get stats
        stats = await BookingService.get_booking_stats(
            db=db_session,
            booking_page_id=booking_page.id
        )

        assert stats is not None
        assert stats["total_bookings"] >= 2
        assert stats["confirmed_bookings"] >= 1
        assert stats["pending_bookings"] >= 1
        assert "confirmation_rate" in stats
