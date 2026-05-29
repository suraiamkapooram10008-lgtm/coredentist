"""
Usage Metering Service
Tracks and calculates usage-based billing metrics

Usage:
    meter = UsageMeter(db)
    meter.record_usage(subscription_id, "api_calls", 1)
    meter.record_usage(subscription_id, "storage_gb", 100)

    # Get current billing period usage
    usage = meter.get_usage_summary(subscription_id)

    # Check if overage applies
    if meter.is_overage(subscription_id, "api_calls"):
        overage_cost = meter.calculate_overage(subscription_id, "api_calls")
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from app.models.subscription import SubscriptionPlan, Subscription, UsageMeter, UsageRecord
from app.models.practice import Practice

logger = logging.getLogger(__name__)


class UsageMeteringService:
    """
    Tracks usage metrics for per-seat/per-use billing

    Metrics tracked:
    - api_calls: Number of API requests
    - storage_gb: Gigabytes of file storage
    - patients: Total patients in system
    - users: Total user seats
    - sms_sent: SMS messages sent
    - email_sent: Emails sent
    - edi_transactions: Insurance EDI submissions
    """

    METRIC_LABELS = {
        "api_calls": ("API Calls", "requests"),
        "storage_gb": ("Storage", "GB"),
        "patients": ("Patients", "patients"),
        "users": ("User Seats", "seats"),
        "sms_sent": ("SMS Sent", "messages"),
        "email_sent": ("Email Sent", "messages"),
        "edi_transactions": ("EDI Transactions", "transactions"),
    }

    def __init__(self, db: Session):
        self.db = db

    def record_usage(
        self,
        subscription_id: str,
        metric_name: str,
        quantity: Decimal,
        description: Optional[str] = None
    ) -> bool:
        """
        Record a usage event

        Args:
            subscription_id: Subscription UUID
            metric_name: Name of the metric (e.g., 'api_calls')
            quantity: Amount to add
            description: Optional description

        Returns:
            True if recorded successfully
        """
        try:
            record = UsageRecord(
                subscription_id=subscription_id,
                meter_id=self._get_meter_id(subscription_id, metric_name),
                quantity=quantity,
                description=description or f"{metric_name}: {quantity}",
                usage_metadata={"metric_name": metric_name}
            )
            self.db.add(record)
            self.db.commit()

            logger.debug(f"Recorded usage: {subscription_id} {metric_name}={quantity}")
            return True

        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
            self.db.rollback()
            return False

    def _get_meter_id(self, subscription_id: str, metric_name: str) -> Optional[str]:
        """Get the meter ID for a subscription and metric"""
        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()

        if not subscription:
            return None

        meter = self.db.query(UsageMeter).join(SubscriptionPlan).filter(
            and_(
                UsageMeter.plan_id == subscription.plan_id,
                UsageMeter.meter_name == metric_name
            )
        ).first()

        return meter.id if meter else None

    def get_usage_summary(
        self,
        subscription_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get usage summary for a subscription in a billing period

        Args:
            subscription_id: Subscription UUID
            period_start: Start of billing period (defaults to start of current month)
            period_end: End of billing period (defaults to end of current month)

        Returns:
            Dict mapping metric_name to usage data
        """
        if period_start is None:
            now = datetime.now(timezone.utc)
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if period_end is None:
            period_end = period_start + timedelta(days=32)
            period_end = period_end.replace(day=1)

        results = self.db.query(
            UsageRecord.usage_metadata,
            func.sum(UsageRecord.quantity).label('total_quantity'),
            func.count(UsageRecord.id).label('event_count')
        ).filter(
            and_(
                UsageRecord.subscription_id == subscription_id,
                UsageRecord.timestamp >= period_start,
                UsageRecord.timestamp < period_end
            )
        ).all()

        usage = {}
        plan = self._get_subscription_plan(subscription_id)
        limits = plan.limits if plan and plan.limits else {}
        overage_rate = Decimal(str(plan.overage_rate)) if plan and plan.is_usage_based else Decimal('0')

        for row in results:
            metadata = row.usage_metadata or {}
            metric = metadata.get('metric_name', 'unknown')
            total = float(row.total_quantity or 0)

            included = Decimal(str(limits.get(metric, 0)))
            overage_quantity = max(0, Decimal(str(total)) - included)
            overage_cost = overage_quantity * overage_rate

            label, unit = self.METRIC_LABELS.get(metric, (metric, "units"))

            usage[metric] = {
                "metric": metric,
                "label": label,
                "unit": unit,
                "total": total,
                "included": float(included),
                "overage_quantity": float(overage_quantity),
                "overage_rate": float(overage_rate),
                "overage_cost": float(overage_cost),
                "is_overage": overage_quantity > 0
            }

        return usage

    def is_overage(
        self,
        subscription_id: str,
        metric_name: str,
        period_start: Optional[datetime] = None
    ) -> bool:
        """Check if subscription is in overage for a metric"""
        summary = self.get_usage_summary(subscription_id, period_start)
        metric_data = summary.get(metric_name, {})
        return metric_data.get("is_overage", False)

    def calculate_overage(
        self,
        subscription_id: str,
        metric_name: str,
        period_start: Optional[datetime] = None
    ) -> Decimal:
        """Calculate overage cost for a metric"""
        summary = self.get_usage_summary(subscription_id, period_start)
        metric_data = summary.get(metric_name, {})
        return Decimal(str(metric_data.get("overage_cost", 0)))

    def get_total_overage(
        self,
        subscription_id: str,
        period_start: Optional[datetime] = None
    ) -> Decimal:
        """Calculate total overage cost across all metrics"""
        summary = self.get_usage_summary(subscription_id, period_start)
        return sum(
            Decimal(str(m.get("overage_cost", 0)))
            for m in summary.values()
        )

    def _get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        return self.db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()

    def _get_subscription_plan(self, subscription_id: str) -> Optional[SubscriptionPlan]:
        """Get the plan for a subscription"""
        subscription = self._get_subscription(subscription_id)
        if subscription:
            return self.db.query(SubscriptionPlan).filter(
                SubscriptionPlan.id == subscription.plan_id
            ).first()
        return None

    def get_usage_for_invoice(
        self,
        subscription_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """
        Get usage data formatted for invoice generation

        Returns:
            Dict with usage details suitable for invoice line items
        """
        usage = self.get_usage_summary(subscription_id, period_start, period_end)
        total_overage = self.get_total_overage(subscription_id, period_start)

        return {
            "subscription_id": subscription_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "metrics": usage,
            "total_overage_amount": float(total_overage),
            "line_items": [
                {
                    "description": f"{data['label']} overage ({data['overage_quantity']} {data['unit']})",
                    "quantity": data['overage_quantity'],
                    "unit_price": data['overage_rate'],
                    "amount": data['overage_cost']
                }
                for data in usage.values()
                if data['is_overage']
            ]
        }


def get_practice_usage_summary(db: Session, practice_id: str) -> Dict[str, Any]:
    """
    Convenience function to get usage summary for a practice
    (finds the active subscription for the practice)
    """
    subscription = db.query(Subscription).filter(
        and_(
            Subscription.practice_id == practice_id,
            Subscription.status == 'active'
        )
    ).first()

    if not subscription:
        return {"error": "No active subscription found"}

    meter_service = UsageMeteringService(db)
    return meter_service.get_usage_summary(str(subscription.id))


class UsageTrackingMiddleware:
    """
    FastAPI middleware to automatically track API usage
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            method = scope.get("method", "")

            if path.startswith("/api/v1/") and method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                headers = dict(scope.get("headers", []))
                practice_id = self._extract_practice_id(headers)

                if practice_id:
                    try:
                        from app.core.database import SessionLocal
                        db = SessionLocal()
                        subscription = db.query(Subscription).filter(
                            and_(
                                Subscription.practice_id == practice_id,
                                Subscription.status == 'active'
                            )
                        ).first()

                        if subscription:
                            meter_service = UsageMeteringService(db)
                            meter_service.record_usage(
                                str(subscription.id),
                                "api_calls",
                                Decimal("1"),
                                f"{method} {path}"
                            )
                        db.close()
                    except Exception as e:
                        logger.debug(f"Usage tracking error: {e}")

        await self.app(scope, receive, send)

    def _extract_practice_id(self, headers: Dict) -> Optional[str]:
        """Extract practice_id from authorization token"""
        try:
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                from app.core.security import decode_token
                payload = decode_token(token)
                if payload:
                    return payload.get("practice_id")
        except Exception:
            pass
        return None
