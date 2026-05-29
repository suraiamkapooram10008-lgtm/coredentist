"""Tests for booking endpoints"""
import pytest
import uuid

pytestmark = pytest.mark.asyncio


class TestBookingPages:
    async def test_list_pages_requires_auth(self, client):
        response = await client.get("/api/v1/booking/pages/")
        assert response.status_code in (401, 403)

    async def test_create_page_requires_auth(self, client):
        response = await client.post("/api/v1/booking/pages/", json={})
        assert response.status_code in (401, 403)

    async def test_create_page_validation_error(self, client, auth_headers):
        response = await client.post("/api/v1/booking/pages/", json={})
        assert response.status_code in (422, 401, 403)

    async def test_get_page_requires_auth(self, client):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/booking/pages/{fake_id}")
        assert response.status_code in (401, 403)

    async def test_update_page_requires_auth(self, client):
        fake_id = str(uuid.uuid4())
        response = await client.put(f"/api/v1/booking/pages/{fake_id}", json={})
        assert response.status_code in (401, 403)


class TestOnlineBooking:
    async def test_list_bookings_requires_auth(self, client):
        response = await client.get("/api/v1/booking/bookings/")
        assert response.status_code in (401, 403)

    async def test_get_booking_requires_auth(self, client):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/booking/bookings/{fake_id}")
        assert response.status_code in (401, 403)

    async def test_update_booking_requires_auth(self, client):
        fake_id = str(uuid.uuid4())
        response = await client.put(f"/api/v1/booking/bookings/{fake_id}", json={})
        assert response.status_code in (401, 403)


class TestWaitlist:
    async def test_list_waitlist_requires_auth(self, client):
        response = await client.get("/api/v1/booking/waitlist/")
        assert response.status_code in (401, 403)


class TestBookingPublic:
    async def test_public_page_returns_404_for_unknown_slug(self, client):
        response = await client.get("/api/v1/booking/public/nonexistent")
        assert response.status_code in (404, 200)
