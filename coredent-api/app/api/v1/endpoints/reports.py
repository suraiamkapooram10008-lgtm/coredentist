"""
Reports Endpoints
Aggregation logic for dashboard and clinic analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, date, timedelta
from typing import Any
import math

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.appointment import Appointment, AppointmentStatus, AppointmentTypeEnum, Chair
from app.models.billing import Invoice, Payment, PaymentStatus
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
) -> Any:
    """
    Get aggregated dashboard metrics for the practice
    """
    practice_id = current_user.practice_id
    
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
            func.date(Appointment.start_time) >= from_date,
            func.date(Appointment.start_time) <= to_date
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
            func.date(Appointment.start_time) >= from_date,
            func.date(Appointment.start_time) <= to_date
        )
    ).group_by(Appointment.appointment_type)
    
    type_res = await db.execute(type_stmt)
    by_type = [
        {"type": t.replace('_', ' ').capitalize(), "count": c, "color": "#3B82F6"} 
        for t, c in type_res.all()
    ]
    
    day_stmt = select(
        func.date(Appointment.start_time).label('day'),
        func.count(Appointment.id).label('count')
    ).where(
        and_(
            Appointment.practice_id == practice_id,
            func.date(Appointment.start_time) >= from_date,
            func.date(Appointment.start_time) <= to_date
        )
    ).group_by(func.date(Appointment.start_time))
    
    day_res = await db.execute(day_stmt)
    days_data = {str(d): c for d, c in day_res.all()}
    
    # Fill in gaps for all days in range
    by_day = []
    curr = from_date
    while curr <= to_date:
        d_str = str(curr)
        by_day.append({"day": d_str, "count": days_data.get(d_str, 0)})
        curr += timedelta(days=1)

    # 2. Revenue Metrics (SQL-Level Aggregation)
    revenue_stmt = select(
        func.sum(Invoice.total).label('revenue'),
        func.sum(Invoice.amount_paid).label('collected'),
        func.sum(Invoice.balance_due).label('outstanding')
    ).where(
        and_(
            Invoice.practice_id == practice_id,
            func.date(Invoice.created_at) >= from_date,
            func.date(Invoice.created_at) <= to_date
        )
    )
    rev_res = await db.execute(revenue_stmt)
    rev_metrics = rev_res.one()
    
    total_revenue = float(rev_metrics.revenue or 0)
    total_collected = float(rev_metrics.collected or 0)
    total_outstanding = float(rev_metrics.outstanding or 0)
    avg_per_visit = (total_revenue / completed) if completed > 0 else 0

    # byMonth aggregation
    # (Simplified: just grouping by current range)
    by_month = [] # Logic for multi-month can be added if range is large

    # 3. Treatment Acceptance (SQL-Level Aggregation)
    plan_stmt = select(
        func.count(TreatmentPlan.id).label('proposed'),
        func.sum(case((TreatmentPlan.status.in_([TreatmentPlanStatus.ACCEPTED, TreatmentPlanStatus.IN_PROGRESS, TreatmentPlanStatus.COMPLETED]), 1)), else_=0).label('accepted'),
        func.sum(case((TreatmentPlan.status == TreatmentPlanStatus.COMPLETED, 1)), else_=0).label('completed_plans')
    ).where(
        and_(
            TreatmentPlan.practice_id == practice_id,
            func.date(TreatmentPlan.created_date) >= from_date,
            func.date(TreatmentPlan.created_date) <= to_date
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
    
    # Simplified utilization logic
    avg_util = 65.0 # Mocking complex calc for now
    
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
            "totalRevenue": total_revenue,
            "totalCollected": total_collected,
            "totalOutstanding": total_outstanding,
            "averagePerVisit": round(avg_per_visit, 2),
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
