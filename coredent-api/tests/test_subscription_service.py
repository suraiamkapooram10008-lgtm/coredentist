"""Unit tests for subscription service pure functions and mocked async methods."""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.services.subscription_service import SubscriptionService
from app.models.subscription import SubscriptionInterval


class TestCalculatePeriodStartEnd:
    def test_weekly(self):
        start, end = SubscriptionService.calculate_period_start_end(
            SubscriptionInterval.WEEKLY,
            datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc)
        )
        assert start.weekday() == 0
        assert (end - start).days == 7

    def test_monthly(self):
        start, end = SubscriptionService.calculate_period_start_end(
            SubscriptionInterval.MONTHLY,
            datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc)
        )
        assert start.day == 1
        assert end > start
        assert end.month == 6

    def test_quarterly(self):
        start, end = SubscriptionService.calculate_period_start_end(
            SubscriptionInterval.QUARTERLY,
            datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc)
        )
        assert start.month in (1, 4, 7, 10)
        assert end > start

    def test_annual(self):
        start, end = SubscriptionService.calculate_period_start_end(
            SubscriptionInterval.ANNUAL,
            datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc)
        )
        assert start.month == 1 and start.day == 1
        assert end.year == 2024

    def test_semi_annual(self):
        start, end = SubscriptionService.calculate_period_start_end(
            SubscriptionInterval.SEMI_ANNUAL,
            datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc)
        )
        assert start.month == 1
        assert end.year == 2024


class TestCalculateProrationAmount:
    def test_basic_proration(self):
        result = SubscriptionService.calculate_proration_amount(
            Decimal("100.00"), Decimal("150.00"), 15, 30
        )
        assert result == Decimal("25.00")

    def test_zero_days_total(self):
        result = SubscriptionService.calculate_proration_amount(
            Decimal("100.00"), Decimal("150.00"), 15, 0
        )
        assert result == Decimal("0")

    def test_negative_proration(self):
        result = SubscriptionService.calculate_proration_amount(
            Decimal("200.00"), Decimal("100.00"), 15, 30
        )
        assert result == Decimal("-50.00")


@pytest.mark.asyncio
class TestGetSubscriptionWithPlan:
    async def test_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"id": "sub-1"}
        mock_db.execute.return_value = mock_result

        result = await SubscriptionService.get_subscription_with_plan(
            mock_db, "550e8400-e29b-41d4-a716-446655440000", "660e8400-e29b-41d4-a716-446655440000"
        )
        assert result == {"id": "sub-1"}
        mock_db.execute.assert_called_once()

    async def test_not_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await SubscriptionService.get_subscription_with_plan(
            mock_db, "550e8400-e29b-41d4-a716-446655440000", "660e8400-e29b-41d4-a716-446655440000"
        )
        assert result is None


@pytest.mark.asyncio
class TestGetUsageRecords:
    async def test_returns_records(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = ["record1", "record2"]
        mock_db.execute.return_value = mock_result

        result = await SubscriptionService.get_usage_records(
            mock_db, "550e8400-e29b-41d4-a716-446655440000"
        )
        assert result == ["record1", "record2"]
