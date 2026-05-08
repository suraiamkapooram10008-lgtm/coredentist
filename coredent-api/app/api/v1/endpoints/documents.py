"""
Documents and Digital Intake Forms API
Manages document templates, patient forms, and e-signatures
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import List, Any
import datetime

from app.api.deps import get_db, get_current_user, get_current_practice
from app.models.user import User
from app.models.practice import Practice
from app.models.document import Document, DocumentTemplate, DocumentStatus, DocumentCategory, DocumentSignature, SignatureStatus

router = APIRouter()

# ── Templates ─────────────────────────────────────────────────────────

@router.get("/templates")
def list_templates(
    db: Session = Depends(get_db),
    current_practice: Practice = Depends(get_current_practice)
):
    """List document templates (Intake forms, consents, etc)"""
    templates = db.query(DocumentTemplate).filter(
        DocumentTemplate.practice_id == current_practice.id
    ).all()
    
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
def list_documents(
    db: Session = Depends(get_db),
    current_practice: Practice = Depends(get_current_practice)
):
    """List patient documents"""
    docs = db.query(Document).filter(
        Document.practice_id == current_practice.id
    ).order_by(Document.created_at.desc()).all()
    
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
def create_document(
    patient_id: str,
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_practice: Practice = Depends(get_current_practice)
):
    """Assign a form template to a patient"""
    template = db.query(DocumentTemplate).get(template_id)
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
    
    db.commit()
    return {"status": "success", "id": str(doc.id)}
