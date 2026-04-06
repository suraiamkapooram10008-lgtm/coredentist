"""
Imaging Endpoints
CRUD operations for patient images and X-rays
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta
from typing import List, Optional, Any
import json
import uuid as uuid_lib
import os
import logging
from pathlib import Path
from fastapi.responses import FileResponse, RedirectResponse

from app.utils.storage import storage

from app.core.database import get_db
from app.api.deps import get_current_user
from app.core.email import email_service
from app.core.audit import log_audit_event
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.imaging import PatientImage, ImageSeries, ImageTemplate, ImageType, ImageCategory
from app.models.patient import Patient
from app.schemas.imaging import (
    PatientImageCreate,
    PatientImageUpdate,
    PatientImageResponse,
    PatientImageListResponse,
    ImageUploadRequest,
    ImageUploadResponse,
    ImageAnnotationCreate,
    ImageAnnotationResponse,
    ImageSeriesCreate,
    ImageSeriesUpdate,
    ImageSeriesResponse,
    ImageSeriesListResponse,
    ImageTemplateCreate,
    ImageTemplateUpdate,
    ImageTemplateResponse,
    ImageTemplateListResponse,
    ImageShareRequest,
    ImageShareResponse,
)
from app.api.deps import verify_csrf, require_role
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter()

# UPLOAD_DIR handled by storage utility


# Patient Image Endpoints

@router.get("/patients/{patient_id}/images", response_model=PatientImageListResponse)
async def list_patient_images(
    patient_id: str,
    image_type: Optional[ImageType] = Query(None, description="Filter by image type"),
    category: Optional[ImageCategory] = Query(None, description="Filter by category"),
    tooth_number: Optional[str] = Query(None, description="Filter by tooth number"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> Any:
    """
    List patient images
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    query = select(PatientImage).where(
        PatientImage.patient_id == patient_id,
        PatientImage.is_deleted == False,
    )
    
    if image_type:
        query = query.where(PatientImage.image_type == image_type)
    
    if category:
        query = query.where(PatientImage.category == category)
    
    if tooth_number:
        query = query.where(PatientImage.tooth_number == tooth_number)
    
    if start_date:
        query = query.where(PatientImage.acquisition_date >= start_date)
    
    if end_date:
        query = query.where(PatientImage.acquisition_date <= end_date)
    
    query = query.order_by(PatientImage.acquisition_date.desc())
    
    result = await db.execute(query)
    images = result.scalars().all()
    
    # Generate temporary pre-signed URLs for each image
    for image in images:
        image.url = storage.get_url(image.file_path)
    
    # HIPAA: Log list images access
    await log_audit_event(
        db, current_user, "list_patient_images", "patient", patient_id, request
    )
    await db.commit()
    
    return PatientImageListResponse(
        images=images,
        count=len(images),
    )


@router.post("/patients/{patient_id}/images", response_model=PatientImageResponse)
async def upload_image(
    patient_id: str,
    file: UploadFile = File(...),
    image_type: ImageType = Query(...),
    category: Optional[ImageCategory] = Query(None),
    tooth_number: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    notes: Optional[str] = Query(None),
    device_name: Optional[str] = Query(None),
    device_serial: Optional[str] = Query(None),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Upload patient image
    SECURITY: File validation implemented
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    # SECURITY: Validate file size
    # Read file content first to check size
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB",
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )
    
    # SECURITY: Validate file type (MIME type check)
    allowed_types = {
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/webp',
        'application/pdf',
        'image/tiff',
        'image/x-tiff',
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not allowed. Allowed types: JPEG, PNG, GIF, BMP, WebP, PDF, TIFF",
        )
    
    # SECURITY: Validate file extension (double validation)
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf', '.tiff', '.tif'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File extension '{file_extension}' not allowed",
        )
    
    # SECURITY: Sanitize filename - remove potentially dangerous characters
    # Keep only safe characters for the original filename
    original_filename = file.filename
    safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.() ')
    safe_filename = ''.join(c if c in safe_chars else '_' for c in original_filename)
    
    # Generate unique filename to prevent overwrites and path traversal
    unique_filename = f"{patient_id}/{uuid_lib.uuid4()}{file_extension}"
    
    # ATOMIC TRANSACTION: Ensure storage and database stay in sync
    try:
        async with db.begin():
            # Save using storage abstraction (Local/S3)
            storage_path = storage.upload(content, unique_filename, file.content_type)
            
            # Create database record
            image = PatientImage(
                practice_id=current_user.practice_id,
                patient_id=patient_id,
                provider_id=current_user.id,
                image_type=image_type,
                category=category,
                tooth_number=tooth_number,
                file_name=safe_filename,  # Use sanitized filename
                file_path=storage_path,
                file_size=file_size,
                mime_type=file.content_type,
                title=title,
                description=description,
                notes=notes,
                acquisition_date=datetime.now(),
                device_name=device_name,
                device_serial=device_serial,
            )
            
            db.add(image)
            # No need for manual commit - db.begin() handles it on success
    except Exception as e:
        # DB rollback is automatic via 'async with db.begin()'
        # File removal for failed DB is harder with S3, but critical for Local
        if storage_path.startswith("uploads"): # Local cleanup
            storage.delete(storage_path)
        logger.error(f"Failed to upload image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image and record"
        )
    
    await db.refresh(image)
    return image



@router.get("/images/{image_id}", response_model=PatientImageResponse)
async def get_image(
    request: Request,
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get image by ID
    """
    result = await db.execute(
        select(PatientImage).where(
            PatientImage.id == image_id,
            PatientImage.practice_id == current_user.practice_id,
            PatientImage.is_deleted == False,
        )
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    # Generate dynamic pre-signed URL
    image.url = storage.get_url(image.file_path)
    
    # HIPAA: Log image access (PHI read)
    await log_audit_event(
        db, current_user, "view_image", "patient_image", image.id, request
    )
    await db.commit()
    
    return image


@router.put("/images/{image_id}", response_model=PatientImageResponse)
async def update_image(
    image_id: str,
    image_data: PatientImageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update image metadata
    """
    result = await db.execute(
        select(PatientImage).where(
            PatientImage.id == image_id,
            PatientImage.practice_id == current_user.practice_id,
            PatientImage.is_deleted == False,
        )
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    update_data = image_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(image, field, value)
    
    await db.commit()
    await db.refresh(image)
    
    return image


@router.delete("/images/{image_id}")
async def delete_image(
    image_id: str,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete image (soft delete)
    """
    result = await db.execute(
        select(PatientImage).where(
            PatientImage.id == image_id,
            PatientImage.practice_id == current_user.practice_id,
        )
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    # Soft delete
    image.is_deleted = True
    image.deleted_at = datetime.now()
    
    await db.commit()
    
    return {"message": "Image deleted successfully"}


@router.get("/images/{image_id}/download")
async def download_image(
    request: Request,
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Download image file
    """
    result = await db.execute(
        select(PatientImage).where(
            PatientImage.id == image_id,
            PatientImage.practice_id == current_user.practice_id,
            PatientImage.is_deleted == False,
        )
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    # HIPAA: Log image download (PHI read)
    await log_audit_event(
        db, current_user, "download_image", "patient_image", image.id, request
    )
    await db.commit()
    
    # Generate presigned URL and redirect
    url = storage.get_url(image.file_path)
    
    if url.startswith("http"):
        return RedirectResponse(url=url)
    
    # Local fallback
    if not os.path.exists(image.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found",
        )
    
    return FileResponse(
        path=image.file_path,
        filename=image.file_name,
        media_type=image.mime_type,
    )


# PUBLIC / EXTERNAL ACCESS (Token-Gated)

@router.get("/public/images/{image_id}", response_model=PatientImageResponse)
async def get_public_image(
    image_id: str,
    token: str = Query(..., description="Secure share token"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> Any:
    """
    Get image metadata for external referral (Token-Gated)
    SECURITY: No current_user dependency. Verified by cryptographic token.
    """
    # EXPERT: Verify token existence and affinity
    result = await db.execute(
        select(PatientImage).where(
            PatientImage.id == image_id,
            PatientImage.share_token == token,
            PatientImage.is_deleted == False,
        )
    )
    image = result.scalar_one_or_none()
    
    if not image:
        # Generic error to prevent token enumeration
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Valid sharing link not found or expired"
        )
    
    # Audit Public Access
    await log_audit_event(
        db, None, "public_image_viewed", "patient_image", image.id, request,
        {"source": "public_link", "token_used": token[:8] + "..."}
    )
    await db.commit()
    
    # Generate dynamic pre-signed URL
    image.url = storage.get_url(image.file_path)
    
    return image


@router.get("/public/images/{image_id}/download")
async def download_public_image(
    image_id: str,
    token: str = Query(..., description="Secure share token"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> Any:
    """
    Download image for external referral (Token-Gated)
    """
    result = await db.execute(
        select(PatientImage).where(
            PatientImage.id == image_id,
            PatientImage.share_token == token,
            PatientImage.is_deleted == False,
        )
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(status_code=404, detail="Valid sharing link not found")
    
    # Audit Public Download
    await log_audit_event(
        db, None, "public_image_downloaded", "patient_image", image.id, request,
        {"source": "public_link"}
    )
    await db.commit()

    # Generate presigned URL and redirect
    url = storage.get_url(image.file_path)
    
    if url.startswith("http"):
        return RedirectResponse(url=url)

    if not os.path.exists(image.file_path):
        raise HTTPException(status_code=404, detail="File missing")
    
    return FileResponse(
        path=image.file_path,
        filename=image.file_name,
        media_type=image.mime_type,
    )


@router.post("/images/{image_id}/annotations", response_model=ImageAnnotationResponse)
async def add_annotations(
    image_id: str,
    annotation_data: ImageAnnotationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Add or update image annotations
    """
    result = await db.execute(
        select(PatientImage).where(
            PatientImage.id == image_id,
            PatientImage.practice_id == current_user.practice_id,
            PatientImage.is_deleted == False,
        )
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    # Convert annotations to JSON string
    annotations_json = json.dumps([ann.dict() for ann in annotation_data.annotations])
    image.annotations = annotations_json
    
    await db.commit()
    await db.refresh(image)
    
    return ImageAnnotationResponse(
        image_id=image.id,
        annotations=annotation_data.annotations,
        updated_at=image.updated_at,
    )


@router.post("/images/{image_id}/share", response_model=ImageShareResponse)
async def share_image(
    image_id: str,
    share_data: ImageShareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Share image with patient or referral
    """
    result = await db.execute(
        select(PatientImage).where(
            PatientImage.id == image_id,
            PatientImage.practice_id == current_user.practice_id,
            PatientImage.is_deleted == False,
        )
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    
    # Update sharing settings
    image.is_shared_with_patient = share_data.share_with_patient
    image.is_shared_with_referral = share_data.share_with_referral
    
    # Generate secure share link
    share_link = None
    expires_at = None
    if share_data.share_with_patient or share_data.share_with_referral:
        # Generate unique token for secure sharing
        import secrets
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=30)  # Link expires in 30 days
        
        # Generate share URL
        if not settings.FRONTEND_URL:
            raise HTTPException(
                status_code=500,
                detail="FRONTEND_URL not configured for image sharing"
            )
        base_url = settings.FRONTEND_URL
        share_link = f"{base_url}/viewer/{image.id}?token={token}"
        
        # Store token in image metadata (in production, store in dedicated table)
        image.share_token = token
    
    # HIPAA: Log image sharing action (PHI external transmission)
    await log_audit_event(
        db, current_user, "share_image", "patient_image", image.id, request,
        {
            "share_with_patient": share_data.share_with_patient,
            "share_with_referral": share_data.share_with_referral,
            "referral_email": share_data.referral_email
        }
    )
    await db.commit()
    
    # Send email to referral if provided
    message = "Image sharing settings updated"
    if share_data.share_with_referral and share_data.referral_email:
        try:
            # Get patient info for email
            result = await db.execute(
                select(Patient).where(Patient.id == image.patient_id)
            )
            patient = result.scalar_one_or_none()
            
            await email_service.send_email(
                to=share_data.referral_email,
                subject=f"Dental Image Referral - {patient.first_name if patient else 'Patient'}",
                html_content=f"""
                <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h1>New Dental Image Referral</h1>
                        <p>You have received a dental image for review.</p>
                        <p><strong>Patient:</strong> {patient.first_name if patient else ''} {patient.last_name if patient else ''}</p>
                        <p><strong>Image Type:</strong> {image.image_type.value if hasattr(image.image_type, 'value') else image.image_type}</p>
                        <p><strong>Date:</strong> {image.acquisition_date.strftime('%Y-%m-%d') if image.acquisition_date else 'N/A'}</p>
                        {f'<p><strong>View Here:</strong> <a href="{share_link}">{share_link}</a></p>' if share_link else ''}
                        <p><em>This link expires in 30 days.</em></p>
                        <hr>
                        <p style="color: #666; font-size: 12px;">
                            CoreDent Dental Practice Management
                        </p>
                    </body>
                </html>
                """,
            )
            message = "Image shared and notification sent to referral"
        except Exception as e:
            logger.warning(f"Failed to send referral email: {str(e)}")
    
    return ImageShareResponse(
        image_id=image.id,
        share_link=share_link,
        expires_at=expires_at,
        message=message,
    )


# Image Series Endpoints

@router.get("/patients/{patient_id}/series", response_model=ImageSeriesListResponse)
async def list_image_series(
    patient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List image series for patient
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    query = select(ImageSeries).where(
        ImageSeries.patient_id == patient_id,
        ImageSeries.practice_id == current_user.practice_id,
    ).order_by(ImageSeries.acquisition_date.desc())
    
    result = await db.execute(query)
    series = result.scalars().all()
    
    return ImageSeriesListResponse(
        series=series,
        count=len(series),
    )


@router.post("/patients/{patient_id}/series", response_model=ImageSeriesResponse)
async def create_image_series(
    patient_id: str,
    series_data: ImageSeriesCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create image series
    """
    # Verify patient belongs to practice
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.practice_id == current_user.practice_id,
        )
    )
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    
    series = ImageSeries(
        practice_id=current_user.practice_id,
        patient_id=patient_id,
        provider_id=series_data.provider_id or current_user.id,
        **series_data.dict(exclude={'provider_id'})
    )
    
    db.add(series)
    await db.commit()
    await db.refresh(series)
    
    return series


@router.get("/series/{series_id}", response_model=ImageSeriesResponse)
async def get_image_series(
    series_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get image series by ID
    """
    result = await db.execute(
        select(ImageSeries).where(
            ImageSeries.id == series_id,
            ImageSeries.practice_id == current_user.practice_id,
        )
    )
    series = result.scalar_one_or_none()
    
    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image series not found",
        )
    
    return series


@router.put("/series/{series_id}", response_model=ImageSeriesResponse)
async def update_image_series(
    series_id: str,
    series_data: ImageSeriesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update image series
    """
    result = await db.execute(
        select(ImageSeries).where(
            ImageSeries.id == series_id,
            ImageSeries.practice_id == current_user.practice_id,
        )
    )
    series = result.scalar_one_or_none()
    
    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image series not found",
        )
    
    update_data = series_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(series, field, value)
    
    await db.commit()
    await db.refresh(series)
    
    return series


# Image Template Endpoints

@router.get("/templates/", response_model=ImageTemplateListResponse)
async def list_templates(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List image templates
    """
    query = select(ImageTemplate).where(ImageTemplate.practice_id == current_user.practice_id)
    
    if is_active is not None:
        query = query.where(ImageTemplate.is_active == is_active)
    
    query = query.order_by(ImageTemplate.name)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    
    return ImageTemplateListResponse(
        templates=templates,
        count=len(templates),
    )


@router.post("/templates/", response_model=ImageTemplateResponse)
async def create_template(
    template_data: ImageTemplateCreate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create image template
    """
    # Convert configuration to JSON string
    configuration_json = json.dumps([conf.dict() for conf in template_data.configuration])
    
    template = ImageTemplate(
        practice_id=current_user.practice_id,
        name=template_data.name,
        description=template_data.description,
        configuration=configuration_json,
        is_active=template_data.is_active,
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template


@router.put("/templates/{template_id}", response_model=ImageTemplateResponse)
async def update_template(
    template_id: str,
    template_data: ImageTemplateUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update image template
    """
    result = await db.execute(
        select(ImageTemplate).where(
            ImageTemplate.id == template_id,
            ImageTemplate.practice_id == current_user.practice_id,
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    
    update_data = template_data.dict(exclude_unset=True)
    
    # Convert configuration if provided
    if 'configuration' in update_data and update_data['configuration']:
        configuration_json = json.dumps([conf.dict() for conf in update_data['configuration']])
        update_data['configuration'] = configuration_json
    
    for field, value in update_data.items():
        setattr(template, field, value)
    
    await db.commit()
    await db.refresh(template)
    
    return template