"""
Tests for Payroll and Commissions endpoints
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

class TestPayrollEndpoints:
    """Test Payroll module endpoints"""

    @pytest.mark.asyncio
    async def test_list_timesheets(self, client: AsyncClient, auth_headers):
        """Test listing timesheets"""
        response = await client.get("/api/v1/payroll/timesheets/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "timesheets" in data

    @pytest.mark.asyncio
    async def test_clock_in(self, client: AsyncClient, auth_headers):
        """Test clocking in a user"""
        response = await client.post("/api/v1/payroll/timesheets/clock-in", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "clock_in" in data
        assert "id" in data
        
        # Test clocking in again (should fail)
        response2 = await client.post("/api/v1/payroll/timesheets/clock-in", headers=auth_headers)
        assert response2.status_code == 400

    @pytest.mark.asyncio
    async def test_clock_out(self, client: AsyncClient, auth_headers):
        """Test clocking out a user"""
        # First clock in
        in_resp = await client.post("/api/v1/payroll/timesheets/clock-in", headers=auth_headers)
        if in_resp.status_code == 400:
            # Already clocked in from previous test or something, fetch active
            list_resp = await client.get("/api/v1/payroll/timesheets/?status=pending", headers=auth_headers)
            timesheet_id = list_resp.json()["timesheets"][0]["id"]
        else:
            timesheet_id = in_resp.json()["id"]

        # Then clock out
        response = await client.post("/api/v1/payroll/timesheets/clock-out", json={"break_minutes": 0}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "clock_out" in data

    @pytest.mark.asyncio
    async def test_create_payroll_period(self, client: AsyncClient, auth_headers):
        """Test generating a payroll period"""
        # Create a period for the past week
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        payload = {
            "period_start": start_date.strftime("%Y-%m-%d"),
            "period_end": end_date.strftime("%Y-%m-%d"),
            "pay_date": end_date.strftime("%Y-%m-%d")
        }
        response = await client.post("/api/v1/payroll/periods/", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "open"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_payroll_periods(self, client: AsyncClient, auth_headers):
        """Test listing payroll periods"""
        response = await client.get("/api/v1/payroll/periods/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "periods" in data
        assert isinstance(data["periods"], list)
