"""
Enterprise & Multi-Practice Endpoints
Consolidated analytics and management for practice groups
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.practice import PracticeGroup, Practice
from app.models.billing import Invoice
from app.models.patient import Patient
from app.models.appointment import Appointment

router = APIRouter()

@router.get("/group/analytics", response_model=Any)
async def get_group_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_role(UserRole.GROUP_OWNER, UserRole.GROUP_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get consolidated analytics for all practices in the group.
    EXPERTISE: Multi-practice aggregation with per-location breakdown.
    """
    # 1. Identity Practice Group (Simplified: User belongs to a practice, which belongs to a group)
    # In production, Group Admins/Owners would have a direct group_id on their user profile.
    result = await db.execute(
        select(Practice).where(Practice.id == current_user.practice_id)
    )
    user_practice = result.scalar_one_or_none()
    
    if not user_practice or not user_practice.group_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an enterprise practice group"
        )
    
    group_id = user_practice.group_id
    
    # Defaults
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
        
    # 2. Get all practices in group
    result = await db.execute(
        select(Practice).where(Practice.group_id == group_id)
    )
    practices = result.scalars().all()
    practice_ids = [p.id for p in practices]
    
    # 3. Aggregated Metrics
    analytics = []
    
    for practice in practices:
        # Production (Total Invoiced)
        prod_result = await db.execute(
            select(func.sum(Invoice.total)).where(
                and_(
                    Invoice.practice_id == practice.id,
                    Invoice.created_at >= start_date,
                    Invoice.created_at <= end_date
                )
            )
        )
        total_production = prod_result.scalar() or 0
        
        # Collections (Total Paid)
        coll_result = await db.execute(
            select(func.sum(Invoice.amount_paid)).where(
                and_(
                    Invoice.practice_id == practice.id,
                    Invoice.created_at >= start_date,
                    Invoice.created_at <= end_date
                )
            )
        )
        total_collections = coll_result.scalar() or 0
        
        # New Patients
        pat_result = await db.execute(
            select(func.count(Patient.id)).where(
                and_(
                    Patient.practice_id == practice.id,
                    Patient.created_at >= start_date,
                    Patient.created_at <= end_date
                )
            )
        )
        new_patients = pat_result.scalar() or 0
        
        # Appointment Utilization
        # Simplified: Ratio of completed vs scheduled
        app_result = await db.execute(
            select(
                func.count(Appointment.id),
                func.count(Appointment.id).filter(Appointment.status == 'completed')
            ).where(
                and_(
                    Appointment.practice_id == practice.id,
                    Appointment.start_time >= start_date,
                    Appointment.start_time <= end_date
                )
            )
        )
        total_apps, completed_apps = app_result.one()
        util_rate = (completed_apps / total_apps * 100) if total_apps > 0 else 0
        
        analytics.append({
            "practice_id": str(practice.id),
            "practice_name": practice.name,
            "production": float(total_production),
            "collections": float(total_collections),
            "new_patients": new_patients,
            "utilization": round(util_rate, 2)
        })
        
    return {
        "group_id": str(group_id),
        "period": {
            "start": start_date,
            "end": end_date
        },
        "consolidated": {
            "production": sum(a["production"] for a in analytics),
            "collections": sum(a["collections"] for a in analytics),
            "new_patients": sum(a["new_patients"] for a in analytics),
            "avg_utilization": sum(a["utilization"] for a in analytics) / len(analytics) if analytics else 0
        },
        "by_location": analytics
    }

@router.get("/group/practices", response_model=List[Any])
async def list_group_practices(
    current_user: User = Depends(require_role(UserRole.GROUP_OWNER, UserRole.GROUP_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List all practice locations within the DSO group.
    """
    result = await db.execute(
        select(Practice).where(Practice.id == current_user.practice_id)
    )
    user_practice = result.scalar_one_or_none()
    
    if not user_practice or not user_practice.group_id:
        raise HTTPException(status_code=403, detail="Enterprise access required")
        
    result = await db.execute(
        select(Practice).where(Practice.group_id == user_practice.group_id)
    )
    return result.scalars().all()
