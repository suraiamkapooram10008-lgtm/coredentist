"""Tests for the scheduled hard purge of anonymized patients.

Covers docs/DATA_RETENTION_POLICY.md § 2: the purge only fires for
fully-anonymized marker rows whose last billing disposition is past the
retention window; explicit deletes (payment cards, plans, portal sessions)
run before the ORM cascade; every purge writes a write-once patient_purged
audit row (certificate of destruction).
"""
import datetime

import pytest

pytestmark = pytest.mark.asyncio


class TestRetentionPurgeEligibility:
    """Pure eligibility logic (no DB needed)."""

    def test_past_window_is_eligible(self):
        from app.services.retention_service import RetentionService

        anchor = datetime.datetime(2010, 1, 1, tzinfo=datetime.timezone.utc)
        now = datetime.datetime(2020, 1, 2, tzinfo=datetime.timezone.utc)
        assert RetentionService.is_eligible_for_purge(
            anchor, now=now, retention_years=7
        )

    def test_recent_anchor_is_not_eligible(self):
        from app.services.retention_service import RetentionService

        now = datetime.datetime(2026, 9, 11, tzinfo=datetime.timezone.utc)
        anchor = now - datetime.timedelta(days=365)
        assert not RetentionService.is_eligible_for_purge(
            anchor, now=now, retention_years=7
        )

    def test_missing_anchor_is_never_eligible(self):
        from app.services.retention_service import RetentionService

        now = datetime.datetime(2026, 9, 11, tzinfo=datetime.timezone.utc)
        assert not RetentionService.is_eligible_for_purge(
            None, now=now, retention_years=7
        )



class TestRetentionPurgeHappyPath:
    """Full purge of an old anonymized patient with billing history."""

    async def test_purges_anonymized_patient_past_window(
        self, async_client, db_session, test_practice, test_user
    ):
        from decimal import Decimal

        from app.models.patient import Patient, PatientStatus
        from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentMethod, PaymentStatus
        from app.services.retention_service import RetentionService
        import uuid as uuid_lib

        # Anonymized marker row (exactly what POST /patients/{id}/anonymize writes).
        patient = Patient(
            id=uuid_lib.uuid4(),
            practice_id=test_practice.id,
            first_name="[deleted]",
            last_name="[deleted]",
            date_of_birth=datetime.date(1970, 1, 1),
            status=PatientStatus.INACTIVE,
        )
        db_session.add(patient)
        await db_session.flush()

        # Old invoice + old payment (8 years ago, past the 7y default).
        old_year = datetime.datetime(2018, 3, 4, tzinfo=datetime.timezone.utc)
        invoice = Invoice(
            id=uuid_lib.uuid4(),
            practice_id=test_practice.id,
            patient_id=patient.id,
            invoice_number="INV-R1",
            status=InvoiceStatus.PAID,
            subtotal=Decimal("100.00"),
            tax=Decimal("0"),
            total=Decimal("100.00"),
            line_items=[{"description": "Cleaning", "quantity": 1, "unit_price": 100.0, "total": 100.0}],
            created_at=old_year,
            updated_at=old_year,
        )
        db_session.add(invoice)
        await db_session.flush()
        payment = Payment(
            id=uuid_lib.uuid4(),
            invoice_id=invoice.id,
            patient_id=patient.id,
            practice_id=test_practice.id,
            amount=Decimal("100.00"),
            refunded_amount=Decimal("0"),
            payment_method=PaymentMethod.CASH,
            transaction_id="TXN-PURGE-1",
            status=PaymentStatus.COMPLETED,
            created_at=old_year,
        )
        db_session.add(payment)
        await db_session.commit()

        anchor = await RetentionService.billing_anchor_async(db_session, patient)
        assert anchor is not None
        now = datetime.datetime(2026, 9, 11, tzinfo=datetime.timezone.utc)
        assert RetentionService.is_eligible_for_purge(anchor, now=now, retention_years=7)

        eligible = await RetentionService.eligible_anonymized_patients(
            db_session, now=now, retention_years=7, limit=1000
        )
        assert any(e["patient_id"] == patient.id for e in eligible)

        result = await RetentionService.purge_patient_hard_async(db_session, patient)
        await db_session.commit()
        assert result["practice_id"] == str(test_practice.id)
        assert result["deleted"]["patients"] == 1

        # Marker row + invoice + payment are gone.
        remaining = await db_session.get(Patient, patient.id)
        assert remaining is None
        inv = await db_session.get(Invoice, invoice.id)
        assert inv is None
        pay = await db_session.get(Payment, payment.id)
        assert pay is None

    async def test_recently_anonymized_patient_is_not_purged(
        self, db_session, test_practice
    ):
        from app.models.patient import Patient, PatientStatus
        from app.services.retention_service import RetentionService
        import uuid as uuid_lib

        patient = Patient(
            id=uuid_lib.uuid4(),
            practice_id=test_practice.id,
            first_name="[deleted]",
            last_name="[deleted]",
            date_of_birth=datetime.date(1970, 1, 1),
            status=PatientStatus.INACTIVE,
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db_session.add(patient)
        await db_session.commit()

        now = datetime.datetime(2026, 9, 11, tzinfo=datetime.timezone.utc)
        eligible = await RetentionService.eligible_anonymized_patients(
            db_session, now=now, retention_years=7, limit=1000
        )
        assert all(e["patient_id"] != patient.id for e in eligible)


class TestRetentionPurgeAsyncShape:
    """The async purge path shares sync ordering; exercise it on a fresh marker."""

    async def test_async_purge_removes_marker_patient(
        self, db_session, test_practice
    ):
        from app.models.patient import Patient, PatientStatus
        from app.services.retention_service import RetentionService
        import uuid as uuid_lib

        marker = Patient(
            id=uuid_lib.uuid4(),
            practice_id=test_practice.id,
            first_name="[deleted]",
            last_name="[deleted]",
            date_of_birth=datetime.date(1970, 1, 1),
            status=PatientStatus.INACTIVE,
        )
        db_session.add(marker)
        await db_session.flush()

        result = await RetentionService.purge_patient_hard_async(db_session, marker)
        await db_session.commit()
        assert result["deleted"]["patients"] == 1
        assert await db_session.get(Patient, marker.id) is None


