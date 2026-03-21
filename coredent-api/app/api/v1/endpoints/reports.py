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

router = APIRouter()

@router.get("/dashboard", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    request: Request,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get aggregated dashboard metrics for the practice
    """
    practice_id = current_user.practice_id
    
    # HIPAA Audit Logging
    await log_audit_event(
        db=db,
        user_id=str(current_user.id),
        action="read",
        entity_type="reports",
        entity_id="dashboard",
        changes={"from": str(from_date), "to": str(to_date)},
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )

    # 1. Appointment Metrics
    appt_query = select(Appointment).where(
        and_(
            Appointment.practice_id == practice_id,
            func.date(Appointment.start_time) >= from_date,
            func.date(Appointment.start_time) <= to_date
        )
    )
    appt_result = await db.execute(appt_query)
    appts = appt_result.scalars().all()
    
    total_appts = len(appts)
    completed = sum(1 for a in appts if a.status == AppointmentStatus.COMPLETED)
    cancelled = sum(1 for a in appts if a.status == AppointmentStatus.CANCELLED)
    no_show = sum(1 for a in appts if a.status == AppointmentStatus.NO_SHOW)
    scheduled = sum(1 for a in appts if a.status == AppointmentStatus.SCHEDULED)
    
    completion_rate = (completed / total_appts * 100) if total_appts > 0 else 0
    no_show_rate = (no_show / total_appts * 100) if total_appts > 0 else 0
    
    # Appointment by Type (mocking colors for now)
    types_count = {}
    for a in appts:
        types_count[a.appointment_type.value] = types_count.get(a.appointment_type.value, 0) + 1
    
    by_type = [
        {"type": t.replace('_', ' ').capitalize(), "count": c, "color": "#3B82F6"} 
        for t, c in types_count.items()
    ]
    
    # Appointment by Day
    days_count = {}
    curr = from_date
    while curr <= to_date:
        days_count[curr.strftime('%Y-%m-%d')] = 0
        curr += timedelta(days=1)
        
    for a in appts:
        d_str = a.start_time.strftime('%Y-%m-%d')
        if d_str in days_count:
            days_count[d_str] += 1
            
    by_day = [{"day": d, "count": c} for d, c in days_count.items()]

    # 2. Revenue Metrics
    invoice_query = select(Invoice).where(
        and_(
            Invoice.practice_id == practice_id,
            func.date(Invoice.created_at) >= from_date,
            func.date(Invoice.created_at) <= to_date
        )
    )
    inv_result = await db.execute(invoice_query)
    invoices = inv_result.scalars().all()
    
    total_revenue = sum(float(i.total) for i in invoices)
    total_collected = sum(i.amount_paid for i in invoices)
    total_outstanding = sum(i.balance_due for i in invoices)
    avg_per_visit = (total_revenue / completed) if completed > 0 else 0

    # byMonth aggregation
    # (Simplified: just grouping by current range)
    by_month = [] # Logic for multi-month can be added if range is large

    # 3. Treatment Acceptance
    plan_query = select(TreatmentPlan).where(
        and_(
            TreatmentPlan.practice_id == practice_id,
            func.date(TreatmentPlan.created_date) >= from_date,
            func.date(TreatmentPlan.created_date) <= to_date
        )
    )
    plan_result = await db.execute(plan_query)
    plans = plan_result.scalars().all()
    
    proposed = len(plans)
    accepted = sum(1 for p in plans if p.status in [TreatmentPlanStatus.ACCEPTED, TreatmentPlanStatus.IN_PROGRESS, TreatmentPlanStatus.COMPLETED])
    completed_plans = sum(1 for p in plans if p.status == TreatmentPlanStatus.COMPLETED)
    
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
