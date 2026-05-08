"""
Payroll Endpoints
Employee compensation, time tracking, commission management, payroll processing, and PTO
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timezone, date
from typing import Optional, Any
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_user, require_role, verify_csrf
from app.models.user import User, UserRole
from app.core.audit import log_audit_event
from app.models.payroll import (
    EmployeeCompensation, CommissionStructure, Timesheet, PayrollPeriod,
    PayrollEntry, ProductionLog, PTOBalance, PTORequest,
    TimesheetStatus, PayrollPeriodStatus, PTORequestStatus,
)
from app.schemas.payroll import (
    CompensationCreate, CommissionStructureCreate, TimesheetClockIn,
    TimesheetClockOut, PayrollPeriodCreate, PTORequestCreate,
    TimesheetResponse, PayrollPeriodResponse,
)
from app.services.payroll_service import PayrollService

router = APIRouter()


# --- Compensation ---
@router.get("/compensation/")
async def list_compensation(
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(
        select(EmployeeCompensation).where(
            EmployeeCompensation.practice_id == current_user.practice_id,
            EmployeeCompensation.is_active == True,
        ).order_by(EmployeeCompensation.effective_date.desc())
    )
    return {"compensation": result.scalars().all()}


@router.post("/compensation/")
async def create_compensation(
    data: CompensationCreate,
    current_user: User = Depends(require_role(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    comp = EmployeeCompensation(practice_id=current_user.practice_id, **data.model_dump())
    db.add(comp)
    await db.commit()
    await db.refresh(comp)
    return comp


@router.put("/compensation/{comp_id}")
async def update_compensation(
    comp_id: str, data: dict,
    current_user: User = Depends(require_role(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    result = await db.execute(
        select(EmployeeCompensation).where(
            EmployeeCompensation.id == comp_id,
            EmployeeCompensation.practice_id == current_user.practice_id,
        )
    )
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Compensation record not found")
    for k, v in data.items():
        setattr(comp, k, v)
    await db.commit()
    await db.refresh(comp)
    return comp


# --- Commission Structures ---
@router.get("/commissions/structures/")
async def list_commission_structures(
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(
        select(CommissionStructure).where(
            CommissionStructure.practice_id == current_user.practice_id,
            CommissionStructure.is_active == True,
        )
    )
    return {"structures": result.scalars().all()}


@router.post("/commissions/structures/")
async def create_commission_structure(
    data: CommissionStructureCreate,
    current_user: User = Depends(require_role(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    structure = CommissionStructure(practice_id=current_user.practice_id, **data.model_dump())
    db.add(structure)
    await db.commit()
    await db.refresh(structure)
    return structure


# --- Time Tracking ---
@router.get("/timesheets/")
async def list_timesheets(
    user_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = select(Timesheet).where(Timesheet.practice_id == current_user.practice_id)
    # Non-admin users can only see their own timesheets
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        query = query.where(Timesheet.user_id == current_user.id)
    elif user_id:
        query = query.where(Timesheet.user_id == user_id)
    if start_date:
        query = query.where(Timesheet.work_date >= start_date)
    if end_date:
        query = query.where(Timesheet.work_date <= end_date)
    if status_filter:
        query = query.where(Timesheet.status == status_filter)
    query = query.order_by(Timesheet.work_date.desc(), Timesheet.clock_in.desc())
    result = await db.execute(query)
    return {"timesheets": result.scalars().all()}


@router.post("/timesheets/clock-in", response_model=TimesheetResponse)
async def clock_in(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    try:
        timesheet = await PayrollService.clock_in(db, current_user)
        await log_audit_event(db, current_user, "clock_in", "timesheet", timesheet.id, request)
        await db.commit()
        return timesheet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/timesheets/clock-out", response_model=TimesheetResponse)
async def clock_out(
    data: TimesheetClockOut,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    try:
        timesheet = await PayrollService.clock_out(db, current_user, data.break_minutes)
        await log_audit_event(db, current_user, "clock_out", "timesheet", timesheet.id, request)
        await db.commit()
        return timesheet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/timesheets/{timesheet_id}/approve", response_model=TimesheetResponse)
async def approve_timesheet(
    timesheet_id: str,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    result = await db.execute(
        select(Timesheet).where(
            Timesheet.id == timesheet_id,
            Timesheet.practice_id == current_user.practice_id,
        )
    )
    ts = result.scalar_one_or_none()
    if not ts:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    ts.status = TimesheetStatus.APPROVED
    ts.approved_by = current_user.id
    ts.approved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(ts)
    return ts


# --- Payroll Periods ---
@router.get("/periods/")
async def list_payroll_periods(
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(
        select(PayrollPeriod).where(
            PayrollPeriod.practice_id == current_user.practice_id
        ).order_by(PayrollPeriod.period_start.desc())
    )
    return {"periods": result.scalars().all()}


@router.post("/periods/", response_model=PayrollPeriodResponse)
async def create_payroll_period(
    data: PayrollPeriodCreate,
    current_user: User = Depends(require_role(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    period = PayrollPeriod(practice_id=current_user.practice_id, **data.model_dump())
    db.add(period)
    await db.commit()
    await db.refresh(period)
    return period


@router.post("/periods/{period_id}/process", response_model=PayrollPeriodResponse)
async def process_payroll(
    period_id: str, request: Request,
    current_user: User = Depends(require_role(UserRole.OWNER)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    result = await db.execute(
        select(PayrollPeriod).where(
            PayrollPeriod.id == period_id,
            PayrollPeriod.practice_id == current_user.practice_id,
        )
    )
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Payroll period not found")
    if period.status == PayrollPeriodStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Payroll period already processed")

    period = await PayrollService.process_payroll(db, period, current_user.practice_id, current_user.id)
    await log_audit_event(db, current_user, "process_payroll", "payroll_period", period.id, request)
    await db.commit()
    return period


@router.get("/periods/{period_id}/entries")
async def get_payroll_entries(
    period_id: str,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(
        select(PayrollEntry).where(PayrollEntry.payroll_period_id == period_id)
    )
    return {"entries": result.scalars().all()}


# --- Production ---
@router.get("/production/")
async def get_production(
    start_date: date = Query(...),
    end_date: date = Query(...),
    user_id: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = select(ProductionLog).where(
        and_(
            ProductionLog.practice_id == current_user.practice_id,
            ProductionLog.service_date >= start_date,
            ProductionLog.service_date <= end_date,
        )
    )
    if user_id:
        query = query.where(ProductionLog.user_id == user_id)
    query = query.order_by(ProductionLog.service_date.desc())
    result = await db.execute(query)
    return {"production_logs": result.scalars().all()}


@router.get("/production/summary")
async def get_production_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    summaries = await PayrollService.get_production_summary(
        db, current_user.practice_id, start_date, end_date
    )
    return {"summaries": summaries}


# --- PTO ---
@router.get("/pto/balances")
async def get_pto_balances(
    user_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = select(PTOBalance).where(PTOBalance.practice_id == current_user.practice_id)
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        query = query.where(PTOBalance.user_id == current_user.id)
    elif user_id:
        query = query.where(PTOBalance.user_id == user_id)
    result = await db.execute(query)
    return {"balances": result.scalars().all()}


@router.post("/pto/requests")
async def create_pto_request(
    data: PTORequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    req = PTORequest(
        user_id=current_user.id,
        practice_id=current_user.practice_id,
        **data.model_dump()
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@router.post("/pto/requests/{request_id}/approve")
async def approve_pto_request(
    request_id: str, action: str = Query(..., regex="^(approve|reject)$"),
    rejection_reason: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    result = await db.execute(
        select(PTORequest).where(
            PTORequest.id == request_id,
            PTORequest.practice_id == current_user.practice_id,
        )
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="PTO request not found")

    if action == "approve":
        req.status = PTORequestStatus.APPROVED
        req.approved_by = current_user.id
        req.approved_at = datetime.now(timezone.utc)
    else:
        req.status = PTORequestStatus.REJECTED
        req.rejection_reason = rejection_reason

    await db.commit()
    await db.refresh(req)
    return req
