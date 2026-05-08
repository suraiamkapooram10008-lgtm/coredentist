"""
Documents and Digital Intake Forms API
Manages document templates, patient forms, and e-signatures
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Any
import datetime
import uuid

from app.api.deps import get_db, get_current_user, get_current_practice
from app.models.user import User
from app.models.practice import Practice
from app.models.document import Document, DocumentTemplate, DocumentStatus, DocumentCategory, DocumentSignature, SignatureStatus

router = APIRouter()

# ── Templates ─────────────────────────────────────────────────────────

@router.get("/templates")
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_practice: Practice = Depends(get_current_practice)
):
    """List document templates (Intake forms, consents, etc)"""
    result = await db.execute(
        select(DocumentTemplate).where(
            DocumentTemplate.practice_id == current_practice.id
        )
    )
    templates = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "type": t.category.value if hasattr(t.category, 'value') else str(t.category),
            "lastUpdated": t.updated_at.strftime("%b %d, %Y"),
            "usage": t.times_used or 0
        }
        for t in templates
    ]

# ── Documents (Forms) ──────────────────────────────────────────────────

@router.get("/")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_practice: Practice = Depends(get_current_practice)
):
    """List patient documents"""
    result = await db.execute(
        select(Document).where(
            Document.practice_id == current_practice.id
        ).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()

    return [
        {
            "id": str(d.id),
            "name": d.name,
            "patient": f"{d.patient.first_name} {d.patient.last_name}" if d.patient else "Unknown",
            "type": d.category.value if hasattr(d.category, 'value') else str(d.category),
            "status": "Signed" if d.is_completed else ("Pending Signature" if d.status == DocumentStatus.PENDING else "Draft"),
            "date": d.created_at.strftime("%b %d, %Y")
        }
        for d in docs
    ]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_document(
    patient_id: uuid.UUID,
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Assign a form template to a patient"""
    result = await db.execute(
        select(DocumentTemplate).where(DocumentTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(404, "Template not found")

    doc = Document(
        practice_id=current_practice.id,
        patient_id=patient_id,
        template_id=template_id,
        created_by=current_user.id,
        name=template.name,
        category=template.category,
        content=template.template_content,
        status=DocumentStatus.PENDING,
        is_completed=False
    )
    db.add(doc)

    # Increment usage
    template.times_used = (template.times_used or 0) + 1

    await db.commit()
    await db.refresh(doc)
    return {"status": "success", "id": str(doc.id)}
