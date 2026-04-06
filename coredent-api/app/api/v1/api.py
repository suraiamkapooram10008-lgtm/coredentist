"""
API Router
Combines all endpoint routers
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    patients,
    appointments,
    billing,
    insurance,
    imaging,
    treatment,
    booking,
    inventory,
    labs,
    referrals,
    reports,
    payments,
    edi,
    accounting,
    staff,
)

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(insurance.router, prefix="/insurance", tags=["Insurance"])
api_router.include_router(imaging.router, prefix="/imaging", tags=["Imaging"])
api_router.include_router(treatment.router, prefix="/treatment", tags=["Treatment Planning"])
api_router.include_router(booking.router, prefix="/booking", tags=["Online Booking"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory Management"])
api_router.include_router(labs.router, prefix="/labs", tags=["Lab Management"])
api_router.include_router(referrals.router, prefix="/referrals", tags=["Referral Management"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reporting & Analytics"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(edi.router, prefix="/edi", tags=["Insurance EDI"])
api_router.include_router(accounting.router, prefix="/accounting", tags=["Accounting Integration"])
api_router.include_router(staff.router, prefix="/staff", tags=["Practice Staff Management"])
