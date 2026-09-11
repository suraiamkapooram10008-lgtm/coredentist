"""
Enterprise & Multi-Practice Endpoints
Consolidated analytics and management for practice groups
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.business_time import (
    DateRangeError,
    get_practice_timezone,
    resolve_instant_range,
)
from app.core.database import get_db
from app.models.appointment import Appointment
from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus
from app.models.patient import Patient
from app.models.practice import Practice
from app.models.user import User, UserRole

class PracticeAnalytics(BaseModel):
    practice_id: str
    practice_name: str
    production: float
    collections: float
    new_patients: int
    utilization: float

class Period(BaseModel):
    start: datetime
    end: datetime

class ConsolidatedMetrics(BaseModel):
    production: float
    collections: float
    new_patients: int
    avg_utilization: float

class GroupAnalyticsResponse(BaseModel):
    group_id: str
    period: Period
    consolidated: ConsolidatedMetrics
    by_location: List[PracticeAnalytics]

class GroupPracticeResponse(BaseModel):
    """Public shape of a practice in a group listing.

    NOTE: response_model must be a Pydantic model — using the SQLAlchemy
    ``Practice`` model raised FastAPIError at import time.
    """
    id: str
    name: str
    address_city: Optional[str] = None
    address_state: Optional[str] = None

router = APIRouter()

_DEFAULT_ANALYTICS_RANGE_DAYS = 30
_DEFAULT_PAGE_SIZE = 50
_MAX_PAGE_SIZE = 100

# M-2 FIX: the billable-invoice statuses used by reports.py ("M12 FIX:
# revenue counts only billable invoices"). DRAFT and CANCELLED totals must
# not count toward group production, matching the practice dashboard.
_BILLABLE_INVOICE_STATUSES = (
    InvoiceStatus.PENDING,
    InvoiceStatus.PARTIALLY_PAID,
    InvoiceStatus.PAID,
    InvoiceStatus.OVERDUE,
)


@router.get("/group/analytics", response_model=GroupAnalyticsResponse)
async def get_group_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_role(UserRole.GROUP_OWNER, UserRole.GROUP_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> GroupAnalyticsResponse:
    """Get consolidated analytics for every practice in the caller's group."""
    # Group membership is derived only from the authenticated caller's practice.
    result = await db.execute(
        select(Practice).where(Practice.id == current_user.practice_id)
    )
    user_practice = result.scalar_one_or_none()

    if not user_practice or not user_practice.group_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an enterprise practice group",
        )

    tz = await get_practice_timezone(db, current_user.practice_id)
    try:
        window = resolve_instant_range(
            tz,
            start_date,
            end_date,
            default_days=_DEFAULT_ANALYTICS_RANGE_DAYS,
            max_days=366,
        )
    except DateRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    group_id = user_practice.group_id
    result = await db.execute(
        select(Practice).where(Practice.group_id == group_id)
    )
    practices = result.scalars().all()

    analytics = []
    for practice in practices:
        # Production (Total Invoiced). M-2 FIX: count only billable invoices —
        # DRAFT and CANCELLED totals used to inflate group production while
        # every other money surface (reports.py "M12 FIX", billing summary)
        # excludes them. Group analytics must not disagree with the practice
        # dashboard for the same period.
        prod_result = await db.execute(
            select(func.sum(Invoice.total)).where(
                and_(
                    Invoice.practice_id == practice.id,
                    Invoice.status.in_(_BILLABLE_INVOICE_STATUSES),
                    Invoice.created_at >= window.start_utc,
                    Invoice.created_at < window.end_utc,
                )
            )
        )
        total_production = prod_result.scalar() or 0

        # Collections (Total Paid). amount_paid is a Python @property, not a
        # column — aggregate completed/refunded Payment rows instead.
        # M-2 FIX: net-of-refunds over (COMPLETED, REFUNDED), exactly like
        # reports.py and billing.py. The previous COMPLETED-only raw sum (a)
        # ignored refunds, overstating collections after any refund, and
        # (b) double-counted REFUNDED rows' residual value differently from
        # every other surface. Refunded amounts subtract; a fully refunded
        # payment contributes zero.
        coll_result = await db.execute(
            select(
                func.sum(
                    Payment.amount - func.coalesce(Payment.refunded_amount, 0)
                )
            )
            .join(Invoice, Payment.invoice_id == Invoice.id)
            .where(
                and_(
                    Invoice.practice_id == practice.id,
                    Payment.status.in_(
                        (
                            PaymentStatus.COMPLETED,
                            PaymentStatus.REFUNDED,
                            PaymentStatus.PARTIALLY_REFUNDED,
                        )
                    ),
                    Payment.created_at >= window.start_utc,
                    Payment.created_at < window.end_utc,
                )
            )
        )
        total_collections = coll_result.scalar() or 0

        # New Patients
        pat_result = await db.execute(
            select(func.count(Patient.id)).where(
                and_(
                    Patient.practice_id == practice.id,
                    Patient.created_at >= window.start_utc,
                    Patient.created_at < window.end_utc,
                )
            )
        )
        new_patients = pat_result.scalar() or 0

        # Appointment Utilization: completed appointments over all appointments.
        app_result = await db.execute(
            select(
                func.count(Appointment.id),
                func.count(Appointment.id).filter(Appointment.status == "completed"),
            ).where(
                and_(
                    Appointment.practice_id == practice.id,
                    Appointment.start_time >= window.start_utc,
                    Appointment.start_time < window.end_utc,
                )
            )
        )
        total_apps, completed_apps = app_result.one()
        util_rate = (completed_apps / total_apps * 100) if total_apps > 0 else 0

        analytics.append(
            {
                "practice_id": str(practice.id),
                "practice_name": practice.name,
                "production": float(total_production),
                "collections": float(total_collections),
                "new_patients": new_patients,
                "utilization": round(util_rate, 2),
            }
        )

    return {
        "group_id": str(group_id),
        "period": {
            "start": window.start_utc,
            "end": window.end_utc,
        },
        "consolidated": {
            "production": sum(a["production"] for a in analytics),
            "collections": sum(a["collections"] for a in analytics),
            "new_patients": sum(a["new_patients"] for a in analytics),
            "avg_utilization": (
                sum(a["utilization"] for a in analytics) / len(analytics)
                if analytics
                else 0
            ),
        },
        "by_location": analytics,
    }


@router.get("/group/practices", response_model=List[GroupPracticeResponse])
async def list_group_practices(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(
        _DEFAULT_PAGE_SIZE,
        ge=1,
        le=_MAX_PAGE_SIZE,
        description="Page size (max 100)",
    ),
    response: Response = None,
    current_user: User = Depends(require_role(UserRole.GROUP_OWNER, UserRole.GROUP_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[GroupPracticeResponse]:
    """List group locations with pagination metadata in response headers.

    The legacy response is a bare array, so total/page metadata is exposed as
    additive ``X-Total-Count``, ``X-Page``, and ``X-Page-Size`` headers rather
    than replacing the JSON response shape.
    """
    result = await db.execute(
        select(Practice).where(Practice.id == current_user.practice_id)
    )
    user_practice = result.scalar_one_or_none()

    if not user_practice or not user_practice.group_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enterprise access required",
        )

    filters = [Practice.group_id == user_practice.group_id]
    total = (
        await db.execute(select(func.count(Practice.id)).where(*filters))
    ).scalar_one()
    result = await db.execute(
        select(Practice)
        .where(*filters)
        .order_by(Practice.name, Practice.id)
        .limit(limit)
        .offset((page - 1) * limit)
    )
    practices = result.scalars().all()

    if response is not None:
        response.headers["X-Total-Count"] = str(total)
        response.headers["X-Page"] = str(page)
        response.headers["X-Page-Size"] = str(limit)

    return [
        GroupPracticeResponse(
            id=str(practice.id),
            name=practice.name,
            address_city=practice.address_city,
            address_state=practice.address_state,
        )
        for practice in practices
    ]
