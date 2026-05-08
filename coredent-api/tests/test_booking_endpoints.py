"""
Comprehensive tests for booking endpoints
Focus on increasing coverage from 14% to 60%+
"""
import pytest
import uuid
from datetime import datetime, timedelta, date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestBookingPageEndpoints:
    """Test booking page management endpoints (admin)"""

    @pytest.mark.asyncio
    async def test_list_booking_pages_success(self, client: AsyncClient, auth_headers, db_session, test_practice):
        """Test listing booking pages"""
        # Create a booking page
        from app.models.booking import BookingPage
        
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug="test-booking",
            page_title="Test Booking Page",
            welcome_message="Welcome to our practice",
            allow_new_patients=True,
            allow_existing_patients=True,
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        
        response = await client.get("/api/v1/booking/pages/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "pages" in data
        assert "count" in data
        assert data["count"] >= 1

    @pytest.mark.asyncio
    async def test_list_booking_pages_with_status_filter(self, client: AsyncClient, auth_headers, db_session, test_practice):
        """Test listing booking pages with status filter"""
        from app.models.booking import BookingPage
        
        # Create active page
        active_page = BookingPage(
            practice_id=test_practice.id,
            page_slug="active-booking",
            page_title="Active Page",
            status="active",
        )
        db_session.add(active_page)
        
        # Create inactive page
        inactive_page = BookingPage(
            practice_id=test_practice.id,
            page_slug="inactive-booking",
            page_title="Inactive Page",
            status="inactive",
        )
        db_session.add(inactive_page)
        await db_session.commit()
        
        response = await client.get("/api/v1/booking/pages/?status=active", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(page["status"] == "active" for page in data["pages"])

    @pytest.mark.asyncio
    async def test_list_booking_pages_unauthorized(self, client: AsyncClient):
        """Test listing booking pages without authentication"""
        response = await client.get("/api/v1/booking/pages/")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_booking_page_success(self, client: AsyncClient, auth_headers):
        """Test creating a new booking page"""
        page_data = {
            "page_slug": f"test-booking-{uuid.uuid4().hex[:8]}",
            "page_title": "Test Booking Page",
            "welcome_message": "Welcome to our practice",
            "allow_new_patients": True,
            "allow_existing_patients": True,
            "require_phone_verification": False,
            "require_email_verification": True,
            "booking_window_days": 30,
            "min_notice_hours": 24,
            "max_bookings_per_day": 10,
            "allowed_appointment_types": [],
            "allowed_providers": [],
            "business_hours": {},
            "blocked_dates": [],
            "intake_form_fields": [],
            "require_insurance_info": False,
            "require_medical_history": False,
            "send_confirmation_email": True,
            "send_confirmation_sms": False,
            "send_reminder_email": True,
            "send_reminder_sms": False,
            "reminder_hours_before": 24,
            "status": "active",
        }
        
        response = await client.post("/api/v1/booking/pages/", json=page_data, headers=auth_headers)
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["page_slug"] == page_data["page_slug"]
        assert data["page_title"] == page_data["page_title"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_booking_page_duplicate_slug(self, client: AsyncClient, auth_headers, db_session, test_practice):
        """Test creating booking page with duplicate slug"""
        from app.models.booking import BookingPage
        
        slug = f"duplicate-slug-{uuid.uuid4().hex[:8]}"
        
        # Create first page
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug=slug,
            page_title="First Page",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        
        # Try to create second page with same slug
        page_data = {
            "page_slug": slug,
            "page_title": "Second Page",
            "allow_new_patients": True,
            "allow_existing_patients": True,
            "status": "active",
            "allowed_appointment_types": [],
            "allowed_providers": [],
            "business_hours": {},
            "blocked_dates": [],
            "intake_form_fields": [],
        }
        
        response = await client.post("/api/v1/booking/pages/", json=page_data, headers=auth_headers)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_booking_page_by_id_success(self, client: AsyncClient, auth_headers, db_session, test_practice):
        """Test getting booking page by ID"""
        from app.models.booking import BookingPage
        
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug="get-test-page",
            page_title="Get Test Page",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)
        
        response = await client.get(f"/api/v1/booking/pages/{page.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert str(data["id"]) == str(page.id)
        assert data["page_slug"] == page.page_slug

    @pytest.mark.asyncio
    async def test_get_booking_page_by_id_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent booking page"""
        nonexistent_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/booking/pages/{nonexistent_id}", headers=auth_headers)
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_booking_page_success(self, client: AsyncClient, auth_headers, db_session, test_practice):
        """Test updating booking page"""
        from app.models.booking import BookingPage
        
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug="update-test-page",
            page_title="Original Title",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)
        
        update_data = {
            "page_title": "Updated Title",
            "welcome_message": "Updated welcome message",
            "status": "inactive",
        }
        
        response = await client.put(f"/api/v1/booking/pages/{page.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["page_title"] == "Updated Title"
        assert data["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_delete_booking_page_success(self, client: AsyncClient, auth_headers, db_session, test_practice):
        """Test deleting booking page"""
        from app.models.booking import BookingPage
        
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug="delete-test-page",
            page_title="Delete Test Page",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)
        
        response = await client.delete(f"/api/v1/booking/pages/{page.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "deactivated" in response.json()["message"].lower()


class TestOnlineBookingEndpoints:
    """Test online booking endpoints (admin)"""

    @pytest.mark.asyncio
    async def test_list_online_bookings_success(self, client: AsyncClient, auth_headers, db_session, test_practice, test_patient):
        """Test listing online bookings"""
        from app.models.booking import OnlineBooking, BookingPage
        
        # Create booking page
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug="list-bookings-page",
            page_title="List Bookings Page",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)
        
        # Create online booking
        booking = OnlineBooking(
            practice_id=test_practice.id,
            booking_page_id=page.id,
            patient_id=test_patient.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+1234567890",
            requested_date=date.today() + timedelta(days=7),
            requested_time=datetime.strptime("10:00", "%H:%M").time(),
            status="pending",
        )
        db_session.add(booking)
        await db_session.commit()
        
        response = await client.get("/api/v1/booking/bookings/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_list_online_bookings_with_status_filter(self, client: AsyncClient, auth_headers, db_session, test_practice, test_patient):
        """Test listing online bookings with status filter"""
        from app.models.booking import OnlineBooking, BookingPage
        
        # Create booking page
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug="filter-bookings-page",
            page_title="Filter Bookings Page",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)
        
        # Create pending booking
        pending_booking = OnlineBooking(
            practice_id=test_practice.id,
            booking_page_id=page.id,
            patient_id=test_patient.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+1234567890",
            requested_date=date.today() + timedelta(days=7),
            requested_time=datetime.strptime("10:00", "%H:%M").time(),
            status="pending",
        )
        db_session.add(pending_booking)
        
        # Create confirmed booking
        confirmed_booking = OnlineBooking(
            practice_id=test_practice.id,
            booking_page_id=page.id,
            patient_id=test_patient.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            phone="+1234567891",
            requested_date=date.today() + timedelta(days=8),
            requested_time=datetime.strptime("10:00", "%H:%M").time(),
            status="confirmed",
        )
        db_session.add(confirmed_booking)
        await db_session.commit()
        
        response = await client.get("/api/v1/booking/bookings/?status=pending", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(booking["status"] == "pending" for booking in data["bookings"])

    @pytest.mark.asyncio
    async def test_get_online_booking_by_id_success(self, client: AsyncClient, auth_headers, db_session, test_practice, test_patient):
        """Test getting online booking by ID"""
        from app.models.booking import OnlineBooking, BookingPage
        
        # Create booking page
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug="get-booking-page",
            page_title="Get Booking Page",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)
        
        # Create online booking
        booking = OnlineBooking(
            practice_id=test_practice.id,
            booking_page_id=page.id,
            patient_id=test_patient.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+1234567890",
            requested_date=date.today() + timedelta(days=7),
            requested_time=datetime.strptime("10:00", "%H:%M").time(),
            status="pending",
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        response = await client.get(f"/api/v1/booking/bookings/{booking.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert str(data["id"]) == str(booking.id)
        assert data["email"] == booking.email

    @pytest.mark.asyncio
    async def test_update_online_booking_status(self, client: AsyncClient, auth_headers, db_session, test_practice, test_patient):
        """Test updating online booking status"""
        from app.models.booking import OnlineBooking, BookingPage
        
        # Create booking page
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug="update-booking-page",
            page_title="Update Booking Page",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)
        
        # Create online booking
        booking = OnlineBooking(
            practice_id=test_practice.id,
            booking_page_id=page.id,
            patient_id=test_patient.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+1234567890",
            requested_date=date.today() + timedelta(days=7),
            requested_time=datetime.strptime("10:00", "%H:%M").time(),
            status="pending",
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        
        update_data = {
            "status": "confirmed",
            "notes": "Booking confirmed by admin",
        }
        
        response = await client.put(f"/api/v1/booking/bookings/{booking.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"


class TestPublicBookingEndpoints:
    """Test public booking endpoints (no auth required)"""

    @pytest.mark.asyncio
    async def test_get_public_booking_page_success(self, client: AsyncClient, db_session, test_practice):
        """Test getting public booking page by slug"""
        from app.models.booking import BookingPage
        
        slug = f"public-page-{uuid.uuid4().hex[:8]}"
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug=slug,
            page_title="Public Booking Page",
            welcome_message="Welcome!",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        
        response = await client.get(f"/api/v1/booking/public/{slug}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page_slug"] == slug
        assert data["page_title"] == "Public Booking Page"

    @pytest.mark.asyncio
    async def test_get_public_booking_page_inactive(self, client: AsyncClient, db_session, test_practice):
        """Test getting inactive public booking page"""
        from app.models.booking import BookingPage
        
        slug = f"inactive-page-{uuid.uuid4().hex[:8]}"
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug=slug,
            page_title="Inactive Page",
            status="inactive",
        )
        db_session.add(page)
        await db_session.commit()
        
        response = await client.get(f"/api/v1/booking/public/{slug}")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_public_booking_page_not_found(self, client: AsyncClient):
        """Test getting non-existent public booking page"""
        response = await client.get("/api/v1/booking/public/nonexistent-slug")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_public_booking_success(self, client: AsyncClient, db_session, test_practice):
        """Test creating a public booking"""
        from app.models.booking import BookingPage
        
        slug = f"create-booking-page-{uuid.uuid4().hex[:8]}"
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug=slug,
            page_title="Create Booking Page",
            allow_new_patients=True,
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        
        booking_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": f"john.{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1234567890",
            "date_of_birth": "1990-01-01",
            "requested_date": (date.today() + timedelta(days=7)).isoformat(),
            "requested_time": "10:00:00",
            "notes": "First visit",
            "is_new_patient": True,
        }
        
        response = await client.post(f"/api/v1/booking/public/{slug}/book", json=booking_data)
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_public_booking_validation_error(self, client: AsyncClient, db_session, test_practice):
        """Test creating public booking with invalid data"""
        from app.models.booking import BookingPage
        
        slug = f"validation-page-{uuid.uuid4().hex[:8]}"
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug=slug,
            page_title="Validation Page",
            allow_new_patients=True,
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        
        booking_data = {
            "first_name": "",  # Empty name
            "email": "invalid-email",  # Invalid email
        }
        
        response = await client.post(f"/api/v1/booking/public/{slug}/book", json=booking_data)
        
        assert response.status_code == 422


class TestWaitlistEndpoints:
    """Test waitlist endpoints"""

    @pytest.mark.asyncio
    async def test_list_waitlist_entries_success(self, client: AsyncClient, auth_headers, db_session, test_practice):
        """Test listing waitlist entries"""
        from app.models.booking import WaitlistEntry, BookingPage
        
        # Create booking page
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug="waitlist-page",
            page_title="Waitlist Page",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)
        
        # Create waitlist entry
        entry = WaitlistEntry(
            practice_id=test_practice.id,
            booking_page_id=page.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+1234567890",
            preferred_dates=[date.today().isoformat(), (date.today() + timedelta(days=30)).isoformat()],
            status="active",
        )
        db_session.add(entry)
        await db_session.commit()
        
        response = await client.get("/api/v1/booking/waitlist/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "count" in data

    @pytest.mark.asyncio
    async def test_create_waitlist_entry_public(self, client: AsyncClient, db_session, test_practice):
        """Test creating waitlist entry from public page"""
        from app.models.booking import BookingPage
        
        slug = f"waitlist-public-{uuid.uuid4().hex[:8]}"
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug=slug,
            page_title="Waitlist Public Page",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        
        entry_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": f"jane.{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1234567890",
            "preferred_dates": [date.today().isoformat(), (date.today() + timedelta(days=30)).isoformat()],
            "notes": "Flexible with timing",
        }
        
        response = await client.post(f"/api/v1/booking/public/{slug}/waitlist", json=entry_data)
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"

    @pytest.mark.asyncio
    async def test_update_waitlist_entry_status(self, client: AsyncClient, auth_headers, db_session, test_practice):
        """Test updating waitlist entry status"""
        from app.models.booking import WaitlistEntry, BookingPage
        
        # Create booking page
        page = BookingPage(
            practice_id=test_practice.id,
            page_slug="update-waitlist-page",
            page_title="Update Waitlist Page",
            status="active",
        )
        db_session.add(page)
        await db_session.commit()
        await db_session.refresh(page)
        
        # Create waitlist entry
        entry = WaitlistEntry(
            practice_id=test_practice.id,
            booking_page_id=page.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+1234567890",
            preferred_dates=[date.today().isoformat(), (date.today() + timedelta(days=30)).isoformat()],
            status="active",
        )
        db_session.add(entry)
        await db_session.commit()
        await db_session.refresh(entry)
        
        update_data = {
            "status": "notified",
            "notes": "Called patient",
        }
        
        response = await client.put(f"/api/v1/booking/waitlist/{entry.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "notified"
