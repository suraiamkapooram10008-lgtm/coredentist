"""
Imaging Endpoints (Refactored)
CRUD operations for patient images and X-rays
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional, Any
import logging
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, verify_csrf, require_role
from app.core.audit import log_audit_event
from app.models.user import User, UserRole
from app.models.imaging import ImageType, ImageCategory, PatientImage
from app.models.patient import Patient
from app.schemas.imaging import (
    PatientImageCreate,
    PatientImageUpdate,
    PatientImageResponse,
    PatientImageListResponse,
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
from app.services.imaging_service import ImagingService
from app.services.imaging_processing import (
    ImageFileProcessor,
    ImageSharingProcessor,
    ImageMetadataProcessor,
)
from app.services.imaging_analysis import ImagingAnalysisService
from app.core.email import email_service
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# Patient Image Endpoints
# ============================================

@router.get("/patients/{patient_id}/images", response_model=PatientImageListResponse)
async def list_patient_images(
    patient_id: uuid.UUID,
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
    try:
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
        
        # Get images using service
        images = await ImagingService.get_patient_images(
            db, patient_id, current_user.practice_id,
            image_type, category, tooth_number, start_date, end_date
        )
        
        # Generate URLs for each image
        for image in images:
            image.url = ImageFileProcessor.get_file_url(image.file_path)
        
        # HIPAA: Log list images access
        await log_audit_event(
            db, current_user, "list_patient_images", "patient", patient_id, request
        )
        
        return PatientImageListResponse(
            images=images,
            count=len(images),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing patient images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving images",
        )


@router.post("/upload", response_model=PatientImageResponse)
async def upload_image_top_level(
    file: UploadFile = File(...),
    patient_id: uuid.UUID = Form(...),
    image_type: Optional[ImageType] = Form(None),
    imaging_type: Optional[str] = Form(None),
    category: Optional[ImageCategory] = Form(None),
    tooth_number: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    device_name: Optional[str] = Form(None),
    device_serial: Optional[str] = Form(None),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Upload image via top-level endpoint (delegates to patient-specific upload)"""
    # Support both image_type and imaging_type from form data
    resolved_type = image_type or (ImageType(imaging_type) if imaging_type else None)
    if not resolved_type:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="image_type or imaging_type is required")
    return await upload_image(
        patient_id=patient_id,
        file=file,
        image_type=resolved_type,
        category=category,
        tooth_number=tooth_number,
        title=title,
        description=description,
        notes=notes,
        device_name=device_name,
        device_serial=device_serial,
        request=request,
        current_user=current_user,
        db=db,
    )


@router.get("/images", response_model=PatientImageListResponse)
async def list_all_images(
    image_type: Optional[ImageType] = Query(None, description="Filter by image type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> Any:
    """List all images for the current practice"""
    try:
        result = await db.execute(
            select(PatientImage).where(
                PatientImage.practice_id == current_user.practice_id,
                PatientImage.is_deleted == False,
            ).order_by(PatientImage.created_at.desc())
        )
        images = result.scalars().all()

        if image_type:
            images = [img for img in images if img.image_type == image_type]

        return PatientImageListResponse(
            images=images,
            count=len(images),
        )
    except Exception as e:
        logger.error(f"Error listing images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving images",
        )


@router.get("/types")
async def list_imaging_types(
    current_user: User = Depends(get_current_user),
) -> Any:
    """List available imaging types"""
    return [
        {"value": t.value, "label": t.value.replace("_", " ").title()}
        for t in ImageType
    ]


@router.post("/images/{image_id}/analyze")
async def analyze_image(
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Analyze image (placeholder)"""
    return {"image_id": image_id, "status": "analysis_pending", "findings": []}


@router.post("/patients/{patient_id}/images", response_model=PatientImageResponse)
async def upload_image(
    patient_id: uuid.UUID,
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
    try:
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
        
        # Validate file
        content, file_extension = await ImageFileProcessor.validate_file(file)
        file_size = len(content)
        
        # Sanitize filename
        safe_filename = ImageFileProcessor.sanitize_filename(file.filename)
        
        # Generate unique filename
        unique_filename = ImageFileProcessor.generate_unique_filename(patient_id, file_extension)
        
        # Upload file
        storage_path = await ImageFileProcessor.upload_file(
            content, unique_filename, file.content_type
        )
        
        # Create image record
        image = await ImagingService.create_image(
            db=db,
            practice_id=current_user.practice_id,
            patient_id=patient_id,
            provider_id=current_user.id,
            image_type=image_type,
            file_path=storage_path,
            file_name=safe_filename,
            file_size=file_size,
            mime_type=file.content_type,
            category=category,
            tooth_number=tooth_number,
            title=title,
            description=description,
            notes=notes,
            device_name=device_name,
            device_serial=device_serial,
        )
        
        # HIPAA: Log image upload
        await log_audit_event(
            db, current_user, "upload_image", "patient_image", image.id, request,
            {"file_size": file_size, "mime_type": file.content_type}
        )
        
        return image
        
    except ValueError as e:
        logger.warning(f"File validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if "empty" in str(e).lower() else status.HTTP_413_REQUEST_ENTITY_TOO_LARGE if "too large" in str(e).lower() else status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image",
        )


@router.get("/images/{image_id}", response_model=PatientImageResponse)
async def get_image(
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> Any:
    """
    Get image by ID
    """
    try:
        image = await ImagingService.get_image(db, image_id, current_user.practice_id)
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )
        
        # Generate URL
        image.url = ImageFileProcessor.get_file_url(image.file_path)
        
        # HIPAA: Log image access
        await log_audit_event(
            db, current_user, "view_image", "patient_image", image.id, request
        )
        
        return image
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving image",
        )


@router.put("/images/{image_id}", response_model=PatientImageResponse)
async def update_image(
    image_id: uuid.UUID,
    image_data: PatientImageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update image metadata
    """
    try:
        image = await ImagingService.get_image(db, image_id, current_user.practice_id)
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )
        
        # Update image
        update_data = image_data.dict(exclude_unset=True)
        image = await ImagingService.update_image(db, image_id, **update_data)
        
        return image
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating image",
        )


@router.delete("/images/{image_id}")
async def delete_image(
    image_id: uuid.UUID,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Delete image (soft delete)
    """
    try:
        success = await ImagingService.delete_image(db, image_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )
        
        return {"message": "Image deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting image",
        )


@router.post("/images/{image_id}/annotations", response_model=ImageAnnotationResponse)
async def add_annotations(
    image_id: uuid.UUID,
    annotation_data: ImageAnnotationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Add or update image annotations
    """
    try:
        image = await ImagingService.get_image(db, image_id, current_user.practice_id)
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )
        
        # Add annotations
        annotations_list = [ann.dict() for ann in annotation_data.annotations]
        image = await ImagingService.add_annotations(db, image_id, annotations_list)
        
        return ImageAnnotationResponse(
            image_id=image.id,
            annotations=annotation_data.annotations,
            updated_at=image.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding annotations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding annotations",
        )


@router.post("/images/{image_id}/share", response_model=ImageShareResponse)
async def share_image(
    image_id: uuid.UUID,
    share_data: ImageShareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Share image with patient or referral
    """
    try:
        image = await ImagingService.get_image(db, image_id, current_user.practice_id)
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )
        
        # Update sharing settings
        share_link, expires_at = await ImageSharingProcessor.update_sharing_settings(
            db, image, share_data.share_with_patient, share_data.share_with_referral
        )
        
        # HIPAA: Log image sharing
        await log_audit_event(
            db, current_user, "share_image", "patient_image", image.id, request,
            {
                "share_with_patient": share_data.share_with_patient,
                "share_with_referral": share_data.share_with_referral,
                "referral_email": share_data.referral_email
            }
        )
        
        message = "Image sharing settings updated"
        
        # Send email to referral if provided
        if share_data.share_with_referral and share_data.referral_email:
            try:
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sharing image",
        )


# ============================================
# Public Image Endpoints (Token-Gated)
# ============================================

@router.get("/public/images/{image_id}", response_model=PatientImageResponse)
async def get_public_image(
    image_id: uuid.UUID,
    token: str = Query(..., description="Secure share token"),
    dob: str = Query(..., description="Patient Date of Birth (YYYY-MM-DD) for verification"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> Any:
    """
    Get image metadata for external referral (Token-Gated + DOB Verified)
    CRIT-17 FIX: Implements 2nd factor verification for HIPAA compliance.
    """
    try:
        # 1. Fetch image and verify token
        image = await ImagingService.get_public_image(db, image_id, token)
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Valid sharing link not found or expired",
            )
        
        # 2. Verify Patient DOB (CRIT-17 2nd Factor)
        result = await db.execute(
            select(Patient).where(Patient.id == image.patient_id)
        )
        patient = result.scalar_one_or_none()
        
        # Normalize and compare DOB
        provided_dob = dob.strip()
        expected_dob = patient.date_of_birth.strftime('%Y-%m-%d') if patient and patient.date_of_birth else None
        
        if not expected_dob or provided_dob != expected_dob:
            # Log failed access attempt
            await log_audit_event(
                db, None, "public_image_access_denied", "patient_image", image.id, request,
                {"reason": "dob_mismatch", "token_prefix": token[:4]}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Verification failed. Please ensure the Date of Birth matches.",
            )
        
        # 3. Generate URL and return
        image.url = ImageFileProcessor.get_file_url(image.file_path)
        
        # HIPAA: Log successful public access
        await log_audit_event(
            db, None, "public_image_viewed", "patient_image", image.id, request,
            {"source": "public_link", "token_used": token[:8] + "...", "verified": True}
        )
        
        return image
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving public image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving image",
        )


# ============================================
# Image Series Endpoints
# ============================================

@router.get("/patients/{patient_id}/series", response_model=ImageSeriesListResponse)
async def list_image_series(
    patient_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List image series for a patient
    """
    try:
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
        
        # Get series using service
        series = await ImagingService.get_image_series(db, patient_id, current_user.practice_id)
        
        return ImageSeriesListResponse(
            series=series,
            count=len(series),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing image series: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving series",
        )


@router.post("/patients/{patient_id}/series", response_model=ImageSeriesResponse)
async def create_image_series(
    patient_id: uuid.UUID,
    series_data: ImageSeriesCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Create image series
    """
    try:
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
        
        # Create series
        series = await ImagingService.create_series(
            db=db,
            practice_id=current_user.practice_id,
            patient_id=patient_id,
            provider_id=series_data.provider_id or current_user.id,
            **series_data.dict(exclude={'provider_id'})
        )
        
        return series
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating image series: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating series",
        )


@router.get("/series/{series_id}", response_model=ImageSeriesResponse)
async def get_image_series(
    series_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get image series by ID
    """
    try:
        series = await ImagingService.get_series(db, series_id, current_user.practice_id)
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image series not found",
            )
        
        return series
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving image series: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving series",
        )


@router.put("/series/{series_id}", response_model=ImageSeriesResponse)
async def update_image_series(
    series_id: uuid.UUID,
    series_data: ImageSeriesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update image series
    """
    try:
        series = await ImagingService.get_series(db, series_id, current_user.practice_id)
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image series not found",
            )
        
        # Update series
        update_data = series_data.dict(exclude_unset=True)
        series = await ImagingService.update_series(db, series_id, **update_data)
        
        return series
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating image series: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating series",
        )


# ============================================
# Image Template Endpoints
# ============================================

@router.get("/templates/", response_model=ImageTemplateListResponse)
async def list_templates(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    List image templates
    """
    try:
        templates = await ImagingService.get_templates(db, current_user.practice_id, is_active)
        
        return ImageTemplateListResponse(
            templates=templates,
            count=len(templates),
        )
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving templates",
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
    try:
        # Create template
        template = await ImagingService.create_template(
            db=db,
            practice_id=current_user.practice_id,
            name=template_data.name,
            configuration=[conf.dict() for conf in template_data.configuration],
            description=template_data.description,
            is_active=template_data.is_active,
        )
        
        return template
        
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating template",
        )


@router.put("/templates/{template_id}", response_model=ImageTemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    template_data: ImageTemplateUpdate,
    current_user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
    _csrf: bool = Depends(verify_csrf),
) -> Any:
    """
    Update image template
    """
    try:
        template = await ImagingService.get_template(db, template_id, current_user.practice_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )
        
        # Update template
        update_data = template_data.dict(exclude_unset=True)
        if 'configuration' in update_data and update_data['configuration']:
            update_data['configuration'] = [conf.dict() for conf in update_data['configuration']]
        
        template = await ImagingService.update_template(db, template_id, **update_data)
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating template",
        )
