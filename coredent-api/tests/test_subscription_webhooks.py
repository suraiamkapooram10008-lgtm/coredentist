"""Unit tests for SubscriptionWebhookHandler using mocked async DB."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.services.subscription_webhooks import SubscriptionWebhookHandler
from app.models.subscription import SubscriptionStatus


@pytest.mark.asyncio
class TestHandleSubscriptionCreated:
    async def test_creates_new_subscription(self):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        # Existing subscription check -> none
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        # Practice lookup
        practice = MagicMock()
        practice.id = "practice-1"
        practice_result = MagicMock()
        practice_result.scalar_one_or_none.return_value = practice

        # Plan lookup
        plan = MagicMock()
        plan.id = "plan-1"
        plan.interval = None
        plan_result = MagicMock()
        plan_result.scalar_one_or_none.return_value = plan

        mock_db.execute.side_effect = [existing_result, practice_result, plan_result]

        sub_data = {
            "id": "sub_test_001",
            "customer": "cus_test_001",
            "status": "active",
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
            "metadata": {"practice_id": "practice-1", "plan_id": "plan-1"},
        }

        await SubscriptionWebhookHandler.handle_subscription_created(mock_db, sub_data)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    async def test_skips_existing(self):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_existing = MagicMock()
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = mock_existing
        mock_db.execute.return_value = existing_result

        await SubscriptionWebhookHandler.handle_subscription_created(
            mock_db, {"id": "sub_test_001"}
        )
        mock_db.add.assert_not_called()

    async def test_missing_practice_metadata(self):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = existing_result

        await SubscriptionWebhookHandler.handle_subscription_created(
            mock_db, {"id": "sub_test_002", "metadata": {}}
        )
        mock_db.add.assert_not_called()


@pytest.mark.asyncio
class TestHandleSubscriptionUpdated:
    async def test_updates_status(self):
        mock_sub = MagicMock()
        mock_sub.status = SubscriptionStatus.ACTIVE
        mock_sub.cancel_at_period_end = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sub
        mock_db.execute.return_value = mock_result

        await SubscriptionWebhookHandler.handle_subscription_updated(
            mock_db,
            {
                "id": "sub_test_001",
                "status": "past_due",
                "cancel_at_period_end": True,
                "current_period_end": 1702592000,
            }
        )
        assert mock_sub.status == SubscriptionStatus.PAST_DUE
        assert mock_sub.cancel_at_period_end is True
        mock_db.commit.assert_awaited_once()

    async def test_not_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        await SubscriptionWebhookHandler.handle_subscription_updated(
            mock_db, {"id": "sub_missing"}
        )
        mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
class TestHandleSubscriptionDeleted:
    async def test_cancels_subscription(self):
        mock_sub = MagicMock()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sub
        mock_db.execute.return_value = mock_result

        await SubscriptionWebhookHandler.handle_subscription_deleted(
            mock_db, {"id": "sub_test_001"}
        )
        assert mock_sub.status == SubscriptionStatus.CANCELED
        assert mock_sub.cancel_at_period_end is True
        assert mock_sub.canceled_at is not None
        mock_db.commit.assert_awaited_once()

    async def test_not_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        await SubscriptionWebhookHandler.handle_subscription_deleted(
            mock_db, {"id": "sub_missing"}
        )
        mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
class TestHandleInvoiceSucceeded:
    async def test_activates_subscription(self):
        mock_sub = MagicMock()
        mock_sub.status = SubscriptionStatus.PAST_DUE
        mock_sub.dunning_retry_count = 3
        mock_sub.last_payment_error = "Card declined"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sub
        mock_db.execute.return_value = mock_result

        result = await SubscriptionWebhookHandler.handle_invoice_succeeded(
            mock_db, {"subscription": "sub_test_001"}
        )
        assert result is mock_sub
        assert mock_sub.status == SubscriptionStatus.ACTIVE
        assert mock_sub.dunning_retry_count == 0
        assert mock_sub.last_payment_error is None

    async def test_no_subscription_field(self):
        mock_db = AsyncMock()
        result = await SubscriptionWebhookHandler.handle_invoice_succeeded(
            mock_db, {"id": "inv_1"}
        )
        assert result is None


@pytest.mark.asyncio
class TestHandleInvoiceFailed:
    async def test_sets_past_due(self):
        mock_sub = MagicMock()
        mock_sub.status = SubscriptionStatus.ACTIVE
        mock_sub.dunning_retry_count = 1
        mock_sub.last_payment_error = None

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sub
        mock_db.execute.return_value = mock_result

        result = await SubscriptionWebhookHandler.handle_invoice_failed(
            mock_db,
            {
                "subscription": "sub_test_001",
                "last_payment_error": {"message": "Insufficient funds"},
            }
        )
        assert result is mock_sub
        assert mock_sub.status == SubscriptionStatus.PAST_DUE
        assert mock_sub.dunning_retry_count == 2
        assert "Insufficient funds" in mock_sub.last_payment_error

    async def test_no_subscription(self):
        mock_db = AsyncMock()
        result = await SubscriptionWebhookHandler.handle_invoice_failed(
            mock_db, {"id": "inv_1"}
        )
        assert result is None


@pytest.mark.asyncio
class TestProcessWebhookEvent:
    async def test_subscription_created(self):
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        # Avoid running full creation logic; ensure routing returns True
        original_handler = SubscriptionWebhookHandler.handle_subscription_created
        SubscriptionWebhookHandler.handle_subscription_created = AsyncMock(return_value=None)
        try:
            result = await SubscriptionWebhookHandler.process_webhook_event(
                mock_db,
                {
                    "type": "customer.subscription.created",
                    "data": {"object": {"id": "sub_1", "status": "active"}},
                }
            )
        finally:
            SubscriptionWebhookHandler.handle_subscription_created = original_handler
        assert result is True

    async def test_subscription_updated(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await SubscriptionWebhookHandler.process_webhook_event(
            mock_db,
            {
                "type": "customer.subscription.updated",
                "data": {"object": {"id": "sub_1", "status": "active"}},
            }
        )
        assert result is True

    async def test_unhandled_event(self):
        mock_db = AsyncMock()
        result = await SubscriptionWebhookHandler.process_webhook_event(
            mock_db,
            {"type": "charge.refunded", "data": {"object": {}}},
        )
        assert result is False

    async def test_error_handling(self):
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("DB error")

        result = await SubscriptionWebhookHandler.process_webhook_event(
            mock_db,
            {
                "type": "customer.subscription.created",
                "data": {"object": {"id": "sub_1"}},
            }
        )
        assert result is False
