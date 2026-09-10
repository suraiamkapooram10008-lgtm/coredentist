"""
Reports Endpoints
Aggregation logic for dashboard and clinic analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.core.business_time import (
    DateRangeError,
    day_expr,
    get_practice_timezone,
    get_practice_timezone_name,
    resolve_date_range,
)
from app.models.user import User
from app.models.appointment import Appointment, AppointmentStatus, Chair
from app.models.billing import Invoice, InvoiceStatus, Payment, PaymentStatus
from app.models.treatment import TreatmentPlan, TreatmentPlanStatus
from app.schemas.reports import DashboardMetricsResponse
from app.core.audit import log_audit_event
from app.api.deps import require_role
from app.models.user import UserRole
from sqlalchemy import case

router = APIRouter()


@router.get("/dashboard", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    request: Request,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> DashboardMetricsResponse:
    """
    Get aggregated dashboard metrics for the practice
    """
    practice_id = current_user.practice_id
    practice_tz = await get_practice_timezone(db, practice_id)
    try:
        date_range = resolve_date_range(practice_tz, from_date, to_date)
    except DateRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # Keep grouping (where SQL functions are appropriate) and filtering
    # separate: predicates use index-friendly UTC half-open bounds.
    tz_name = await get_practice_timezone_name(db, practice_id)
    from_date = date_range.start_date
    to_date = date_range.end_date

    appt_day = day_expr(Appointment.start_time, tz_name)
    appointment_range = (
        Appointment.start_time >= date_range.start_utc,
        Appointment.start_time < date_range.end_utc,
    )
    invoice_range = (
        Invoice.created_at >= date_range.start_utc,
        Invoice.created_at < date_range.end_utc,
    )
    payment_range = (
        Payment.created_at >= date_range.start_utc,
        Payment.created_at < date_range.end_utc,
    )




    # HIPAA Audit Logging (Standardized Utility)
    await log_audit_event(
        db, current_user, "dashboard_report_viewed", "report", "dashboard", request,
        {"from": str(from_date), "to": str(to_date)}
    )
    await db.commit()

    # 1. Appointment Metrics (SQL-Level Aggregation for Scalability)
    metrics_stmt = select(
        func.count(Appointment.id).label('total'),
        func.sum(case((Appointment.status == AppointmentStatus.COMPLETED, 1), else_=0)).label('completed'),
        func.sum(case((Appointment.status == AppointmentStatus.CANCELLED, 1), else_=0)).label('cancelled'),
        func.sum(case((Appointment.status == AppointmentStatus.NO_SHOW, 1), else_=0)).label('no_show'),
        func.sum(case((Appointment.status == AppointmentStatus.SCHEDULED, 1), else_=0)).label('scheduled')
    ).where(
        and_(
            Appointment.practice_id == practice_id,
            *appointment_range
        )
    )
    res = await db.execute(metrics_stmt)
    apps_metrics = res.one()

    total_appts = apps_metrics.total or 0
    completed = apps_metrics.completed or 0
    cancelled = apps_metrics.cancelled or 0
    no_show = apps_metrics.no_show or 0
    scheduled = apps_metrics.scheduled or 0

    completion_rate = (completed / total_appts * 100) if total_appts > 0 else 0
    no_show_rate = (no_show / total_appts * 100) if total_appts > 0 else 0

    # 1.5 Appointment by Type & Day (SQL-Level Aggregation)
    type_stmt = select(
        Appointment.appointment_type,
        func.count(Appointment.id).label('count')
    ).where(
        and_(
            Appointment.practice_id == practice_id,
            *appointment_range
        )
    ).group_by(Appointment.appointment_type)

    type_res = await db.execute(type_stmt)
    by_type = [
        {"type": t.replace('_', ' ').capitalize(), "count": c, "color": "#3B82F6"}
        for t, c in type_res.all()
    ]

    from app.core.database import row_locks_supported

    if row_locks_supported():
        day_stmt = select(
            appt_day.label('day'),
            func.count(Appointment.id).label('count')
        ).where(
            and_(
                Appointment.practice_id == practice_id,
                *appointment_range
            )
        ).group_by(appt_day)

        day_res = await db.execute(day_stmt)
        days_data = {str(day): count for day, count in day_res.all()}
    else:
        # SQLite has no IANA-timezone SQL conversion. Bucket its UTC instants
        # in Python so a practice's local calendar date stays authoritative.
        from app.core.business_time import business_date

        start_times = (
            await db.execute(
                select(Appointment.start_time).where(
                    and_(
                        Appointment.practice_id == practice_id,
                        *appointment_range,
                    )
                )
            )
        ).scalars().all()
        days_data = {}
        for start_time in start_times:
            local_day = str(business_date(practice_tz, start_time))
            days_data[local_day] = days_data.get(local_day, 0) + 1

    # Fill in gaps for all days in range
    by_day = []
    curr = from_date
    while curr <= to_date:
        d_str = str(curr)
        by_day.append({"day": d_str, "count": days_data.get(d_str, 0)})
        curr += timedelta(days=1)

    # 2. Revenue Metrics (SQL-Level Aggregation)
    # Note: amount_paid and balance_due are properties, not columns
    # We need to calculate them from the payments table
    # M12 FIX: revenue counts only billable invoices — DRAFT and CANCELLED
    # amounts used to inflate totalOutstanding.
    revenue_stmt = select(
        func.sum(Invoice.total).label('revenue')
    ).where(
        and_(
            Invoice.practice_id == practice_id,
            Invoice.status.in_([
                InvoiceStatus.PENDING,
                InvoiceStatus.PARTIALLY_PAID,
                InvoiceStatus.PAID,
                InvoiceStatus.OVERDUE,
            ]),
            *invoice_range
        )
    )
    rev_res = await db.execute(revenue_stmt)
    rev_metrics = rev_res.one()

    total_revenue = Decimal(str(rev_metrics.revenue or 0))

    # Collections use the date the money moved, not the invoice date. This is
    # the cash basis used by billing summary and prevents a payment made today
    # on an older invoice from disappearing from today's collections.
    collected_stmt = select(
        func.sum(Payment.amount - func.coalesce(Payment.refunded_amount, 0)).label('collected')
    ).join(Invoice).where(
        and_(
            Invoice.practice_id == practice_id,
            *payment_range,
            Payment.status.in_([PaymentStatus.COMPLETED, PaymentStatus.REFUNDED])
        )
    )
    collected_res = await db.execute(collected_stmt)
    collected_metrics = collected_res.one()

    total_collected = Decimal(str(collected_metrics.collected or 0))

    # Outstanding is the current balance of invoices raised in the selected
    # invoice-date window. It includes all completed/refunded payments against
    # those invoices, regardless of when they were received; subtracting only
    # in-window payments was the old source of negative/misleading balances.
    paid_for_invoice = (
        select(func.coalesce(func.sum(
            Payment.amount - func.coalesce(Payment.refunded_amount, 0)
        ), 0))
        .where(
            Payment.invoice_id == Invoice.id,
            Payment.status.in_([PaymentStatus.COMPLETED, PaymentStatus.REFUNDED]),
        )
        .correlate(Invoice)
        .scalar_subquery()
    )
    outstanding_stmt = select(
        func.sum(Invoice.total - paid_for_invoice).label("outstanding")
    ).where(
        and_(
            Invoice.practice_id == practice_id,
            Invoice.status.in_([
                InvoiceStatus.PENDING,
                InvoiceStatus.PARTIALLY_PAID,
                InvoiceStatus.PAID,
                InvoiceStatus.OVERDUE,
            ]),
            *invoice_range,
        )
    )
    outstanding_res = await db.execute(outstanding_stmt)
    total_outstanding = Decimal(str(outstanding_res.scalar() or 0))
    avg_per_visit = (total_revenue / Decimal(str(completed))) if completed > 0 else Decimal('0')

    # byMonth aggregation
    # (Simplified: just grouping by current range)
    # (Multi-month breakdown can be added here if the range is large.)

    # 3. Treatment Acceptance (SQL-Level Aggregation)
    plan_stmt = select(
        func.count(TreatmentPlan.id).label('proposed'),
        func.sum(case((TreatmentPlan.status.in_([TreatmentPlanStatus.ACCEPTED, TreatmentPlanStatus.IN_PROGRESS, TreatmentPlanStatus.COMPLETED]), 1), else_=0)).label('accepted'),
        func.sum(case((TreatmentPlan.status == TreatmentPlanStatus.COMPLETED, 1), else_=0)).label('completed_plans')
    ).where(
        and_(
            TreatmentPlan.practice_id == practice_id,
            TreatmentPlan.created_date >= from_date,
            TreatmentPlan.created_date <= to_date
        )
    )
    plan_res = await db.execute(plan_stmt)
    plan_metrics = plan_res.one()

    proposed = plan_metrics.proposed or 0
    accepted = plan_metrics.accepted or 0
    completed_plans = plan_metrics.completed_plans or 0

    acceptance_rate = (accepted / proposed * 100) if proposed > 0 else 0
    plan_completion_rate = (completed_plans / accepted * 100) if accepted > 0 else 0

    # 4. Chair Utilization
    chair_query = select(Chair).where(Chair.practice_id == practice_id)
    chair_result = await db.execute(chair_query)
    chairs = chair_result.scalars().all()

    days_count = max(1, (to_date - from_date).days + 1)
    num_chairs = max(1, len(chairs))
    total_available_minutes = num_chairs * 8 * 60 * days_count  # 8 operating hours/day

    duration_stmt = select(
        func.coalesce(func.sum(Appointment.duration), 0)
    ).where(
        and_(
            Appointment.practice_id == practice_id,
            *appointment_range,
            Appointment.status.notin_([AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]),
        )
    )
    duration_res = await db.execute(duration_stmt)
    booked_minutes = duration_res.scalar() or 0
    avg_util = min(100.0, round((booked_minutes / total_available_minutes) * 100, 1))

    return {
        "appointments": {
            "total": total_appts,
            "completed": completed,
            "cancelled": cancelled,
            "noShow": no_show,
            "scheduled": scheduled,
            "completionRate": round(completion_rate, 1),
            "noShowRate": round(no_show_rate, 1),
            "byType": by_type,
            "byDay": by_day,
        },
        "revenue": {
            "totalRevenue": str(total_revenue),
            "totalCollected": str(total_collected),
            "totalOutstanding": str(total_outstanding),
            "averagePerVisit": str(round(avg_per_visit, 2)),
            "byMonth": [],
            "byProcedure": [],
        },
        "treatmentAcceptance": {
            "proposedPlans": proposed,
            "acceptedPlans": accepted,
            "completedPlans": completed_plans,
            "acceptanceRate": round(acceptance_rate, 1),
            "completionRate": round(plan_completion_rate, 1),
            "byMonth": [],
        },
        "chairUtilization": {
            "totalChairs": len(chairs),
            "averageUtilization": avg_util,
            "peakHours": [],
            "byChair": [],
            "byDayOfWeek": [],
        }
    }