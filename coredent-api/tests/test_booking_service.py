"""Tests for BookingService with mocked DB."""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, date, time
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.booking_service import BookingService


class TestBookingGenerators:
    def test_generate_confirmation_code(self):
        code = BookingService.generate_confirmation_code()
        assert len(code) == 8
        assert code.isalnum()

    def test_generate_verification_token(self):
        token = BookingService.generate_verification_token()
        assert len(token) > 20

    def test_generate_verification_code(self):
        code = BookingService.generate_verification_code()
        assert len(code) == 6
        assert code.isdigit()


@pytest.mark.asyncio
class TestBookingPageService:
    async def test_create_booking_page(self):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        page = MagicMock(id=uuid4(), page_slug="test-page")

        with patch("app.services.booking_service.BookingPage", return_value=page):
            result = await BookingService.create_booking_page(
                mock_db, uuid4(), "Test Page"
            )
        assert result is page
        assert page.page_slug == "test-page"
        mock_db.commit.assert_awaited_once()

    async def test_get_booking_page(self):
        page = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = page

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await BookingService.get_booking_page(mock_db, uuid4(), practice_id=uuid4())
        assert result is page

    async def test_get_booking_page_no_practice(self):
        page = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = page

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await BookingService.get_booking_page(mock_db, uuid4())
        assert result is page

    async def test_get_public_booking_page(self):
        page = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = page

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await BookingService.get_public_booking_page(mock_db, "my-page")
        assert result is page

    async def test_update_booking_page(self):
        page = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = page

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await BookingService.update_booking_page(
            mock_db, uuid4(), page_title="New Name", status="inactive"
        )
        assert result is page
        assert page.page_title == "New Name"
        assert page.status == "inactive"
        mock_db.commit.assert_awaited_once()

    async def test_update_booking_page_not_found(self):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await BookingService.update_booking_page(mock_db, uuid4(), page_title="X")
        assert result is None


@pytest.mark.asyncio
class TestOnlineBookingService:
    async def test_create_online_booking(self):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        booking = MagicMock(id=uuid4())
        booking_date = date.today()
        booking_time = time(9, 0)

        with patch("app.services.booking_service.OnlineBooking", return_value=booking):
            result = await BookingService.create_online_booking(
                mock_db, uuid4(), uuid4(), "John", "Doe", "john@example.com", "555-1234",
                booking_date, booking_time, reason="checkup"
            )
        assert result is booking
        mock_db.commit.assert_awaited_once()

    async def test_get_online_booking(self):
        booking = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = booking

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await BookingService.get_online_booking(mock_db, uuid4())
        assert result is booking

    async def test_update_online_booking(self):
        booking = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = booking

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await BookingService.update_online_booking(
            mock_db, uuid4(), status="confirmed"
        )
        assert result is booking
        assert booking.status == "confirmed"
        mock_db.commit.assert_awaited_once()

    async def test_confirm_booking(self):
        from app.models.booking import BookingStatus
        booking = MagicMock()
        booking.status = BookingStatus.PENDING
        booking.confirmed_at = None

        mock_db = AsyncMock()
        with patch.object(BookingService, "get_online_booking", return_value=booking):
            result = await BookingService.confirm_booking(mock_db, uuid4(), "123456")
        assert result is True
        assert booking.status == BookingStatus.CONFIRMED
        assert booking.confirmed_at is not None
        mock_db.commit.assert_awaited_once()

    async def test_confirm_booking_not_found(self):
        mock_db = AsyncMock()
        with patch.object(BookingService, "get_online_booking", return_value=None):
            result = await BookingService.confirm_booking(mock_db, uuid4(), "123456")
        assert result is False

    async def test_confirm_booking_empty_code(self):
        booking = MagicMock()
        mock_db = AsyncMock()
        with patch.object(BookingService, "get_online_booking", return_value=booking):
            result = await BookingService.confirm_booking(mock_db, uuid4(), "")
        assert result is False

    async def test_list_bookings(self):
        b1 = MagicMock(status="pending")
        b2 = MagicMock(status="confirmed")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [b1, b2]

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await BookingService.list_bookings(mock_db, uuid4(), status="pending")
        assert len(result) == 2

    async def test_get_booking_stats(self):
        from app.models.booking import BookingStatus, WaitlistStatus
        b1 = MagicMock(status=BookingStatus.CONFIRMED)
        b2 = MagicMock(status=BookingStatus.PENDING)
        w1 = MagicMock(status=WaitlistStatus.ACTIVE)

        mock_db = AsyncMock()
        exec_results = [
            MagicMock(scalars=lambda: MagicMock(all=lambda: [b1, b2])),  # total
            MagicMock(scalars=lambda: MagicMock(all=lambda: [b1])),       # confirmed
            MagicMock(scalars=lambda: MagicMock(all=lambda: [b2])),       # pending
            MagicMock(scalars=lambda: MagicMock(all=lambda: [w1])),       # waitlist
        ]
        mock_db.execute.side_effect = exec_results

        result = await BookingService.get_booking_stats(mock_db, uuid4())
        assert result["total_bookings"] == 2
        assert result["confirmed_bookings"] == 1
        assert result["pending_bookings"] == 1
        assert result["waitlist_count"] == 1
        assert result["confirmation_rate"] == 50.0


@pytest.mark.asyncio
class TestWaitlistService:
    async def test_add_to_waitlist(self):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        entry = MagicMock(id=uuid4())

        with patch("app.services.booking_service.Waitlist", return_value=entry):
            result = await BookingService.add_to_waitlist(
                mock_db, uuid4(), uuid4(), "Jane", "Doe", "jane@example.com", "555-5678"
            )
        assert result is entry
        mock_db.commit.assert_awaited_once()
