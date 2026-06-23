"""
Patient Portal API Endpoints
Public-facing endpoints for patients to view their own data and make payments.
Uses a separate token-based auth flow (magic link / access code).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import secrets
import hashlib

from app.core.database import get_db
from app.core.config_simple import settings
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.billing import Invoice
from app.models.treatment import TreatmentPlan
from app.models.insurance import PatientInsurance

router = APIRouter()


# ── Portal Access Token Utilities ──────────────────────────────────────

def _hash_portal_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ── Portal Authentication ─────────────────────────────────────────────

@router.post("/access")
async def request_portal_access(
    email: str,
    date_of_birth: str,
    practice_slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Patient requests portal access by verifying identity with email + DOB.
    Returns a short-lived portal access token.
    """
    from app.models.practice import Practice

    # Find the practice
    result = await db.execute(
        select(Practice).where(Practice.slug == practice_slug)
    )
    practice = result.scalar_one_or_none()
    if not practice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practice not found")

    # Find patient by email + DOB within that practice
    result = await db.execute(
        select(Patient).where(
            Patient.practice_id == practice.id,
            Patient.email == email.lower().strip(),
            Patient.date_of_birth == date_of_birth,
            Patient.status == "active",
        )
    )
    patient = result.scalar_one_or_none()

    if not patient:
        # Don't reveal whether patient exists (security)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to verify identity. Please contact your dental office.",
        )

    # Generate a portal access token (valid per-session, stored hashed)
    raw_token = secrets.token_urlsafe(48)
    patient.portal_access_token = _hash_portal_token(raw_token)
    patient.portal_token_expires = datetime.now(timezone.utc).replace(
        hour=23, minute=59, second=59
    )  # Expires end of day

    await db.commit()

    return {
        "access_token": raw_token,
        "patient_name": f"{patient.first_name} {patient.last_name}",
        "practice_name": practice.name,
        "expires_at": patient.portal_token_expires.isoformat(),
    }


async def _get_portal_patient(
    token: str,
    db: AsyncSession,
) -> Patient:
    """Verify portal token and return the patient."""
    hashed = _hash_portal_token(token)
    result = await db.execute(
        select(Patient).where(
            Patient.portal_access_token == hashed,
            Patient.status == "active",
        )
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    if patient.portal_token_expires and patient.portal_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired. Please request a new one.",
        )

    return patient


# ── Patient Profile ───────────────────────────────────────────────────

@router.get("/me")
async def get_my_profile(
    token: str = Query(..., description="Portal access token"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the authenticated patient's own profile."""
    patient = await _get_portal_patient(token, db)

    return {
        "id": str(patient.id),
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "email": patient.email,
        "phone": patient.phone,
        "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        "address": patient.address_street,
        "city": patient.address_city,
        "state": patient.address_state,
        "zip_code": patient.address_zip,
    }


# ── Appointments ──────────────────────────────────────────────────────

@router.get("/appointments")
async def get_my_appointments(
    token: str = Query(..., description="Portal access token"),
    upcoming_only: bool = Query(True, description="Show only upcoming appointments"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the patient's appointments."""
    patient = await _get_portal_patient(token, db)

    query = select(Appointment).where(
        Appointment.patient_id == patient.id,
    )

    if upcoming_only:
        query = query.where(
            Appointment.start_time >= datetime.now(timezone.utc)
        )

    query = query.order_by(Appointment.start_time.asc())
    result = await db.execute(query)
    appointments = result.scalars().all()

    return {
        "appointments": [
            {
                "id": str(apt.id),
                "start_time": apt.start_time.isoformat() if apt.start_time else None,
                "end_time": apt.end_time.isoformat() if apt.end_time else None,
                "status": apt.status.value if hasattr(apt.status, 'value') else str(apt.status),
                "reason": apt.appointment_type.value if hasattr(apt.appointment_type, 'value') else str(apt.appointment_type) if apt.appointment_type else None,
                "notes": apt.notes if hasattr(apt, 'notes') else None,
                "provider_name": None,  # Provider name requires join; kept lightweight
            }
            for apt in appointments
        ],
        "count": len(appointments),
    }


# ── Billing & Invoices ───────────────────────────────────────────────

@router.get("/billing")
async def get_my_billing(
    token: str = Query(..., description="Portal access token"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the patient's invoices and outstanding balances."""
    patient = await _get_portal_patient(token, db)

    result = await db.execute(
        select(Invoice).where(
            Invoice.patient_id == patient.id,
        ).order_by(Invoice.created_at.desc())
    )
    invoices = result.scalars().all()

    total_outstanding = sum(
        float(inv.total or 0) - float(inv.amount_paid or 0)
        for inv in invoices
        if inv.status not in ("paid", "cancelled")
    )

    return {
        "total_outstanding": round(total_outstanding, 2),
        "invoices": [
            {
                "id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "date": inv.created_at.isoformat() if inv.created_at else None,
                "total_amount": float(inv.total or 0),
                "amount_paid": float(inv.amount_paid or 0),
                "balance_due": round(float(inv.total or 0) - float(inv.amount_paid or 0), 2),
                "status": inv.status.value if hasattr(inv.status, 'value') else str(inv.status),
                "description": inv.notes,
            }
            for inv in invoices
        ],
        "count": len(invoices),
    }


# ── Treatment Plans ──────────────────────────────────────────────────

@router.get("/treatment-plans")
async def get_my_treatment_plans(
    token: str = Query(..., description="Portal access token"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the patient's treatment plans."""
    patient = await _get_portal_patient(token, db)

    result = await db.execute(
        select(TreatmentPlan).where(
            TreatmentPlan.patient_id == patient.id,
        ).order_by(TreatmentPlan.created_at.desc())
    )
    plans = result.scalars().all()

    return {
        "treatment_plans": [
            {
                "id": str(plan.id),
                "plan_name": plan.plan_name,
                "status": plan.status.value if hasattr(plan.status, 'value') else str(plan.status),
                "total_estimated_cost": float(plan.total_estimated_cost or 0),
                "total_insurance_estimate": float(plan.total_insurance_estimate or 0),
                "total_patient_responsibility": float(plan.total_patient_responsibility or 0),
                "created_date": plan.created_date.isoformat() if plan.created_date else None,
                "diagnosis": plan.diagnosis,
                "treatment_goals": plan.treatment_goals,
            }
            for plan in plans
        ],
        "count": len(plans),
    }


# ── Insurance Info ────────────────────────────────────────────────────

@router.get("/insurance")
async def get_my_insurance(
    token: str = Query(..., description="Portal access token"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the patient's insurance information on file."""
    patient = await _get_portal_patient(token, db)

    result = await db.execute(
        select(PatientInsurance).where(
            PatientInsurance.patient_id == patient.id,
            PatientInsurance.is_active == True,
        )
    )
    insurances = result.scalars().all()

    return {
        "insurance_policies": [
            {
                "id": str(ins.id),
                "insurance_type": ins.insurance_type.value if hasattr(ins.insurance_type, 'value') else str(ins.insurance_type),
                "subscriber_id": ins.subscriber_id,
                "group_number": ins.group_number,
                "effective_date": ins.effective_date.isoformat() if ins.effective_date else None,
                "annual_maximum": float(ins.annual_maximum or 0),
                "annual_deductible": float(ins.annual_deductible or 0),
                "deductible_met": float(ins.deductible_met or 0),
                "preventive_coverage": ins.preventive_coverage,
                "basic_coverage": ins.basic_coverage,
                "major_coverage": ins.major_coverage,
            }
            for ins in insurances
        ],
        "count": len(insurances),
    }


# ── Online Payment ────────────────────────────────────────────────────

@router.post("/pay")
async def make_payment(
    token: str = Query(..., description="Portal access token"),
    invoice_id: str = Query(..., description="Invoice ID to pay"),
    amount: float = Query(..., gt=0, description="Amount to pay"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> dict:
    """
    Patient makes a payment on an invoice.
    In production, this would create a Stripe PaymentIntent.
    """
    patient = await _get_portal_patient(token, db)

    # Verify the invoice belongs to the patient
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.patient_id == patient.id,
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    balance_due = float(invoice.total or 0) - float(invoice.amount_paid or 0)
    if amount > balance_due:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount exceeds balance due of ${balance_due:.2f}",
        )

    # Fail closed when the provider is unavailable; never report an unprocessed payment.
    stripe_key = settings.STRIPE_SECRET_KEY
    if not stripe_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Online payments are not configured. Please contact the practice.",
        )

    payment_intent_id = None
    client_secret = None
    if stripe_key:
        try:
            import stripe as stripe_lib
            stripe_lib.api_key = stripe_key

            intent = stripe_lib.PaymentIntent.create(
                amount=int(amount * 100),
                currency="usd",
                metadata={
                    "invoice_id": str(invoice.id),
                    "patient_id": str(patient.id),
                    "practice_id": str(patient.practice_id),
                },
                description=f"Payment for invoice {invoice_id[:8]}",
            )
            payment_intent_id = intent.id
            client_secret = intent.client_secret
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Payment processing error: {str(e)}",
            )

    return {
        "status": "payment_intent_created" if client_secret else "pending",
        "payment_intent_id": payment_intent_id,
        "client_secret": client_secret,
        "amount": amount,
        "invoice_id": str(invoice.id),
        "message": "Complete payment using the client secret with Stripe.js",
    }


# ── Digital Forms & Documents ─────────────────────────────────────────

@router.get("/documents")
async def get_my_documents(
    token: str = Query(..., description="Portal access token"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get documents and forms assigned to the patient"""
    patient = await _get_portal_patient(token, db)
    from app.models.document import Document

    result = await db.execute(
        select(Document).where(
            Document.patient_id == patient.id,
        ).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()

    return {
        "documents": [
            {
                "id": str(d.id),
                "name": d.name,
                "type": d.category.value if hasattr(d.category, 'value') else str(d.category),
                "is_completed": d.is_completed,
                "content": d.content, # Contains the form fields/HTML
                "assigned_date": d.created_at.isoformat() if d.created_at else None,
                "completed_date": d.completed_at.isoformat() if d.completed_at else None,
            }
            for d in docs
        ],
        "count": len(docs),
    }

@router.post("/documents/{document_id}/sign")
async def sign_document(
    document_id: str,
    signature_data: str = Query(..., description="Base64 image or signature text"),
    token: str = Query(..., description="Portal access token"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Submit an electronic signature for a form"""
    patient = await _get_portal_patient(token, db)
    from app.models.document import Document

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.patient_id == patient.id
        )
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.is_completed = True
    doc.completed_at = datetime.now(timezone.utc)

    db.add(doc)
    await db.commit()

    return {"status": "success", "message": "Document signed successfully"}