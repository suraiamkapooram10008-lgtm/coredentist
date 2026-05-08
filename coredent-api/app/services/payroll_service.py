"""
Payroll Service
Commission calculation engine, payroll processing, and production tracking
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal

from app.models.payroll import (
    EmployeeCompensation, CommissionStructure, Timesheet, PayrollPeriod,
    PayrollEntry, ProductionLog, PTOBalance, PayrollPeriodStatus,
    TimesheetStatus, CommissionType, PayType,
)
from app.models.user import User

import logging
logger = logging.getLogger(__name__)


class CommissionEngine:
    """Calculates commissions based on structure rules"""

    @staticmethod
    def calculate(structure: CommissionStructure, production: float, collections: float,
                  procedure_codes: List[Dict] = None) -> float:
        if not structure:
            return 0.0

        if structure.commission_type == CommissionType.PRODUCTION_PERCENTAGE:
            return float(production * (float(structure.rate_percentage or 0) / 100))

        elif structure.commission_type == CommissionType.COLLECTION_PERCENTAGE:
            return float(collections * (float(structure.rate_percentage or 0) / 100))

        elif structure.commission_type == CommissionType.TIERED:
            return CommissionEngine._calculate_tiered(structure.tiers or [], production)

        elif structure.commission_type == CommissionType.PER_PROCEDURE:
            return CommissionEngine._calculate_per_procedure(
                structure.procedure_rates or {}, procedure_codes or []
            )
        return 0.0

    @staticmethod
    def _calculate_tiered(tiers: List[Dict], amount: float) -> float:
        commission = 0.0
        for tier in sorted(tiers, key=lambda t: t.get("min", 0)):
            tier_min = float(tier.get("min", 0))
            tier_max = float(tier.get("max", float('inf')))
            rate = float(tier.get("rate", 0)) / 100
            if amount > tier_min:
                taxable = min(amount, tier_max) - tier_min
                commission += taxable * rate
        return commission

    @staticmethod
    def _calculate_per_procedure(rates: Dict[str, float], procedures: List[Dict]) -> float:
        commission = 0.0
        for proc in procedures:
            code = proc.get("code", "")
            if code in rates:
                commission += float(rates[code])
        return commission


class PayrollService:
    """Payroll processing and production tracking"""

    @staticmethod
    async def get_employee_compensation(db: AsyncSession, user_id: UUID, practice_id: UUID):
        result = await db.execute(
            select(EmployeeCompensation).where(
                and_(
                    EmployeeCompensation.user_id == user_id,
                    EmployeeCompensation.practice_id == practice_id,
                    EmployeeCompensation.is_active == True,
                )
            ).order_by(EmployeeCompensation.effective_date.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def clock_in(db: AsyncSession, user: User) -> Timesheet:
        # Check for existing open timesheet
        result = await db.execute(
            select(Timesheet).where(
                and_(
                    Timesheet.user_id == user.id,
                    Timesheet.practice_id == user.practice_id,
                    Timesheet.clock_out == None,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("Already clocked in. Please clock out first.")

        now = datetime.now(timezone.utc)
        timesheet = Timesheet(
            user_id=user.id,
            practice_id=user.practice_id,
            work_date=now.date(),
            clock_in=now,
            status=TimesheetStatus.PENDING,
        )
        db.add(timesheet)
        await db.commit()
        await db.refresh(timesheet)
        return timesheet

    @staticmethod
    async def clock_out(db: AsyncSession, user: User, break_minutes: int = 0) -> Timesheet:
        result = await db.execute(
            select(Timesheet).where(
                and_(
                    Timesheet.user_id == user.id,
                    Timesheet.practice_id == user.practice_id,
                    Timesheet.clock_out == None,
                )
            )
        )
        timesheet = result.scalar_one_or_none()
        if not timesheet:
            raise ValueError("Not clocked in.")

        now = datetime.now(timezone.utc)
        timesheet.clock_out = now
        timesheet.break_minutes = break_minutes

        # Calculate hours
        clock_in_time = timesheet.clock_in
        if clock_in_time.tzinfo is None:
            clock_in_time = clock_in_time.replace(tzinfo=timezone.utc)
        delta = (now - clock_in_time).total_seconds() / 3600
        net_hours = max(0, delta - (break_minutes / 60))
        timesheet.total_hours = round(net_hours, 2)

        await db.commit()
        await db.refresh(timesheet)
        return timesheet

    @staticmethod
    async def get_production_summary(
        db: AsyncSession, practice_id: UUID,
        start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Get production summary by provider for a date range"""
        result = await db.execute(
            select(
                ProductionLog.user_id,
                func.sum(ProductionLog.production_amount).label('total_production'),
                func.sum(ProductionLog.collection_amount).label('total_collections'),
                func.count(ProductionLog.id).label('procedures_completed'),
            ).where(
                and_(
                    ProductionLog.practice_id == practice_id,
                    ProductionLog.service_date >= start_date,
                    ProductionLog.service_date <= end_date,
                )
            ).group_by(ProductionLog.user_id)
        )
        rows = result.all()

        summaries = []
        for row in rows:
            prod = float(row.total_production or 0)
            coll = float(row.total_collections or 0)
            procs = int(row.procedures_completed or 0)
            # Get user name
            user_result = await db.execute(select(User).where(User.id == row.user_id))
            user = user_result.scalar_one_or_none()
            summaries.append({
                "user_id": str(row.user_id),
                "user_name": user.full_name if user else "Unknown",
                "role": user.role.value if user else "",
                "total_production": prod,
                "total_collections": coll,
                "collection_rate": round((coll / prod * 100) if prod > 0 else 0, 1),
                "procedures_completed": procs,
                "avg_production_per_procedure": round(prod / procs if procs > 0 else 0, 2),
            })
        return summaries

    @staticmethod
    async def process_payroll(
        db: AsyncSession, period: PayrollPeriod, practice_id: UUID, processed_by: UUID
    ) -> PayrollPeriod:
        """Process payroll for a period — calculate pay for all employees"""
        # Get all active employees with compensation
        result = await db.execute(
            select(EmployeeCompensation).where(
                and_(
                    EmployeeCompensation.practice_id == practice_id,
                    EmployeeCompensation.is_active == True,
                )
            )
        )
        compensations = result.scalars().all()

        total_gross = Decimal(0)
        total_commissions = Decimal(0)

        for comp in compensations:
            # Get timesheets for this employee in the period
            ts_result = await db.execute(
                select(Timesheet).where(
                    and_(
                        Timesheet.user_id == comp.user_id,
                        Timesheet.practice_id == practice_id,
                        Timesheet.work_date >= period.period_start,
                        Timesheet.work_date <= period.period_end,
                        Timesheet.status == TimesheetStatus.APPROVED,
                    )
                )
            )
            timesheets = ts_result.scalars().all()

            regular_hours = sum(float(ts.total_hours or 0) for ts in timesheets)
            overtime_hours = sum(float(ts.overtime_hours or 0) for ts in timesheets)

            # Calculate base pay
            if comp.pay_type == PayType.SALARY:
                # Pro-rate salary for the period
                days_in_period = (period.period_end - period.period_start).days + 1
                base_pay = float(comp.pay_rate) / 365 * days_in_period
            else:
                base_pay = regular_hours * float(comp.pay_rate)

            overtime_pay = overtime_hours * float(comp.pay_rate) * float(comp.overtime_rate_multiplier or 1.5)

            # Calculate commissions
            commission_amount = 0.0
            if comp.commission_enabled and comp.commission_structure_id:
                cs_result = await db.execute(
                    select(CommissionStructure).where(CommissionStructure.id == comp.commission_structure_id)
                )
                structure = cs_result.scalar_one_or_none()
                if structure:
                    prod_result = await db.execute(
                        select(
                            func.sum(ProductionLog.production_amount),
                            func.sum(ProductionLog.collection_amount),
                        ).where(
                            and_(
                                ProductionLog.user_id == comp.user_id,
                                ProductionLog.practice_id == practice_id,
                                ProductionLog.service_date >= period.period_start,
                                ProductionLog.service_date <= period.period_end,
                            )
                        )
                    )
                    prod_row = prod_result.one()
                    production = float(prod_row[0] or 0)
                    collections = float(prod_row[1] or 0)
                    commission_amount = CommissionEngine.calculate(structure, production, collections)

            gross = base_pay + overtime_pay + commission_amount

            entry = PayrollEntry(
                payroll_period_id=period.id,
                user_id=comp.user_id,
                regular_hours=regular_hours,
                overtime_hours=overtime_hours,
                base_pay=round(base_pay, 2),
                overtime_pay=round(overtime_pay, 2),
                commission_amount=round(commission_amount, 2),
                gross_pay=round(gross, 2),
                net_pay=round(gross, 2),  # Simplified — no tax calc
            )
            db.add(entry)
            total_gross += Decimal(str(round(gross, 2)))
            total_commissions += Decimal(str(round(commission_amount, 2)))

        period.total_gross = total_gross
        period.total_commissions = total_commissions
        period.status = PayrollPeriodStatus.CLOSED
        period.processed_by = processed_by
        period.processed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(period)
        return period
