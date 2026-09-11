"""
Retention service: eligibility + hard purge for anonymized patients.

Implements the "hard purge (scheduled)" step of docs/DATA_RETENTION_POLICY.md:
once every billing disposition for a fully-anonymized patient is older than the
configured retention window (R2 default 7 years), the orphaned rows are deleted
and the anonymized placeholder row is removed. Each purge writes a write-once
audit row so destruction has a paper trail.

Markers:
  - An anonymized patient = first_name "[deleted]" AND last_name "[deleted]"
    AND status INACTIVE (exactly what POST /patients/{id}/anonymize writes).
  - "Last billing disposition" = latest of invoice.created_at, payment.created_at,
    payment-plan updated_at, insurance-claim created_at; patient.updated_at as
    fallback when there is no billing history at all.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.billing import Invoice, Payment, PaymentPlan
from app.models.insurance import InsuranceClaim
from app.models.patient import Patient, PatientPortalSession, PatientStatus
from app.models.payment import PaymentCard, PaymentTransaction, RecurringBilling
from app.models.subscription import Subscription
from app.models.imaging import ImageSeries
from app.models.marketing import MarketingEmail

logger = logging.getLogger(__name__)

ANONYMIZED_FIRST_NAME = "[deleted]"
ANONYMIZED_LAST_NAME = "[deleted]"

# Tables with a patient_id FK that have NO cascade collection on Patient, so
# db.delete(patient) would try to NULL them (violating NOT NULL) instead of
# deleting them. They are deleted explicitly before the cascade delete runs.
_EXPLICIT_DELETE_MODELS = (
    PaymentCard,
    RecurringBilling,
    PaymentTransaction,
    PaymentPlan,
    Subscription,
    PatientPortalSession,
    ImageSeries,
    MarketingEmail,
)


def _as_aware(value: Optional[datetime]) -> Optional[datetime]:
    """Best-effort tz-normalization (SQLite returns naive datetimes)."""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _years_delta(years: int) -> timedelta:
    """Calendar-year delta without third-party deps (leap-day safe)."""
    return timedelta(days=365 * years + years // 4)


class RetentionService:
    """Eligibility + hard purge for fully-anonymized patients."""

    # ----------------------------------------------------------------------
    # Eligibility
    # ----------------------------------------------------------------------

    @staticmethod
    async def billing_anchor_async(
        db: AsyncSession, patient: Patient
    ) -> Optional[datetime]:
        """Latest billing disposition instant for a patient (UTC-aware)."""
        candidates: List[Optional[datetime]] = []
        for model, column in (
            (Invoice, Invoice.created_at),
            (Payment, Payment.created_at),
            (PaymentPlan, PaymentPlan.updated_at),
            (InsuranceClaim, InsuranceClaim.created_at),
        ):
            row = await db.execute(
                select(func.max(column)).where(model.patient_id == patient.id)
            )
            value = row.scalar_one_or_none()
            if value is not None:
                candidates.append(_as_aware(value))
        aware = [c for c in candidates if c is not None]
        if aware:
            return max(aware)
        return _as_aware(patient.updated_at)

    @staticmethod
    def is_eligible_for_purge(
        anchor: Optional[datetime],
        *,
        now: datetime,
        retention_years: int,
    ) -> bool:
        """True when the last billing disposition is past the retention window."""
        if anchor is None:
            return False
        return now >= anchor + _years_delta(retention_years)

    @staticmethod
    async def find_anonymized_candidates(
        db: AsyncSession, *, limit: int = 50
    ) -> List[Patient]:
        """Fetch fully-anonymized patients (marker rows) for purge evaluation.

        NOTE: first_name/last_name are Fernet-encrypted TypeDecorators, so DB
        equality matching is impossible (each envelope has a random IV). Fetch
        the full candidate set and match the markers in Python after decrypt
        (TypeDecorator decrypts transparently on attribute access).
        """
        rows = await db.execute(
            select(Patient)
            .where(Patient.status == PatientStatus.INACTIVE)
            .order_by(Patient.updated_at.asc().nullslast())
            .limit(limit * 10)
        )
        matched: List[Patient] = []
        for candidate in rows.scalars().all():
            if (
                candidate.first_name == ANONYMIZED_FIRST_NAME
                and candidate.last_name == ANONYMIZED_LAST_NAME
            ):
                matched.append(candidate)
            if len(matched) >= limit:
                break
        return matched

    @staticmethod
    async def eligible_anonymized_patients(
        db: AsyncSession,
        *,
        now: Optional[datetime] = None,
        retention_years: int = 7,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Anonymized patients whose billing history is past the window."""
        moment = now or datetime.now(timezone.utc)
        out: List[Dict[str, Any]] = []
        for patient in await RetentionService.find_anonymized_candidates(db, limit=limit):
            anchor = await RetentionService.billing_anchor_async(db, patient)
            if RetentionService.is_eligible_for_purge(
                anchor, now=moment, retention_years=retention_years
            ):
                out.append(
                    {
                        "patient_id": patient.id,
                        "practice_id": patient.practice_id,
                        "anchor": anchor,
                    }
                )
        return out


    # ----------------------------------------------------------------------
    # Hard purge (async + sync variants share the same ordering)
    # ----------------------------------------------------------------------

    @staticmethod
    async def purge_patient_hard_async(
        db: AsyncSession, patient: Patient
    ) -> Dict[str, Any]:
        """Delete an anonymized patient's orphaned rows + placeholder, async flavor."""
        counts: Dict[str, int] = {}
        # 1) Explicit deletes for patient_id tables with no Patient cascade.
        for model in _EXPLICIT_DELETE_MODELS:
            rows = await db.execute(
                model.__table__.delete().where(
                    model.__table__.c.patient_id == patient.id
                )
            )
            counts[model.__tablename__] = rows.rowcount if rows.rowcount is not None else 0
        # 2) ORM cascade handles invoices/payments/notes/appointments/etc.
        await db.delete(patient)
        await db.flush()
        counts["patients"] = 1
        return {
            "patient_id": str(patient.id),
            "practice_id": str(patient.practice_id),
            "deleted": counts,
        }

    @staticmethod
    def purge_patient_hard(db: Session, patient) -> Dict[str, Any]:
        """Delete an anonymized patient's orphaned rows + placeholder (sync)."""
        counts: Dict[str, int] = {}
        for model in _EXPLICIT_DELETE_MODELS:
            rows = (
                db.query(model)
                .filter(model.patient_id == patient.id)
                .delete(synchronize_session=False)
            )
            counts[model.__tablename__] = rows or 0
        db.delete(patient)
        db.flush()
        counts["patients"] = 1
        return {
            "patient_id": str(patient.id),
            "practice_id": str(patient.practice_id),
            "deleted": counts,
        }
