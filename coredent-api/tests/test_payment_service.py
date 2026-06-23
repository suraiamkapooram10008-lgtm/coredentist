"""Unit tests for payment service mocked async methods."""
import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.payment_service import PaymentService


@pytest.mark.asyncio
class TestPaymentService:
    async def test_get_invoice_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_invoice = MagicMock()
        mock_invoice.id = uuid4()
        mock_result.scalar_one_or_none.return_value = mock_invoice
        mock_db.execute.return_value = mock_result

        result = await PaymentService.get_invoice(mock_db, uuid4())
        assert result is mock_invoice

    async def test_get_invoice_not_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await PaymentService.get_invoice(mock_db, uuid4())
        assert result is None

    async def test_get_payment_found(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_payment = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_payment
        mock_db.execute.return_value = mock_result

        result = await PaymentService.get_payment(mock_db, "txn_123")
        assert result is mock_payment

    async def test_create_payment_record(self):
        mock_db = AsyncMock()
        mock_invoice = MagicMock()
        mock_invoice.id = uuid4()
        mock_invoice.balance_due = Decimal("100.00")

        # get_invoice side-effect
        async def get_invoice_side_effect(db, invoice_id, practice_id=None):
            return mock_invoice

        # Patch get_invoice inside the service
        original_get_invoice = PaymentService.get_invoice
        PaymentService.get_invoice = staticmethod(get_invoice_side_effect)

        from app.models.payment import PaymentStatus
        try:
            result = await PaymentService.create_payment_record(
                mock_db, mock_invoice.id, uuid4(), 50.00, "card", "txn_123", PaymentStatus.COMPLETED
            )
            assert result is not None
            assert result.invoice_id == mock_invoice.id
        finally:
            PaymentService.get_invoice = original_get_invoice

    async def test_mark_invoice_paid(self):
        mock_db = AsyncMock()
        mock_invoice = MagicMock()
        mock_invoice.id = uuid4()
        mock_invoice.balance_due = Decimal("0.00")
        mock_invoice.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_invoice
        mock_db.execute.return_value = mock_result

        result = await PaymentService.mark_invoice_paid(mock_db, mock_invoice.id)
        assert result is mock_invoice
        assert result.status == "paid"

    async def test_update_payment_status(self):
        mock_db = AsyncMock()
        mock_payment = MagicMock()
        mock_payment.id = uuid4()
        mock_payment.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_payment
        mock_db.execute.return_value = mock_result

        from app.models.payment import PaymentStatus
        result = await PaymentService.update_payment_status(
            mock_db, mock_payment.id, PaymentStatus.COMPLETED
        )
        assert result is mock_payment
        assert result.status == PaymentStatus.COMPLETED

    async def test_list_payments(self):
        mock_db = AsyncMock()
        mock_payments = [MagicMock(), MagicMock()]

        mock_count_result = MagicMock()
        mock_count_result.scalars.return_value.all.return_value = [1, 2]  # two dummy items

        mock_paginated_result = MagicMock()
        mock_paginated_result.scalars.return_value.all.return_value = mock_payments

        mock_db.execute.side_effect = [mock_count_result, mock_paginated_result]

        payments, total = await PaymentService.list_payments(mock_db, uuid4())
        assert payments == mock_payments
        assert total == 2
