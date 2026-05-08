"""
Imaging Service
Core business logic for imaging operations
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.models.imaging import PatientImage, ImageSeries, ImageTemplate, ImageType, ImageCategory
from app.models.patient import Patient

logger = logging.getLogger(__name__)


class ImagingService:
    """Service for imaging operations"""
    
    @staticmethod
    async def get_patient_images(
        db: AsyncSession,
        patient_id: UUID,
        practice_id: UUID,
        image_type: Optional[ImageType] = None,
        category: Optional[ImageCategory] = None,
        tooth_number: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[PatientImage]:
        """Get patient images with filtering"""
        query = select(PatientImage).where(
            PatientImage.patient_id == patient_id,
            PatientImage.practice_id == practice_id,
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
        return result.scalars().all()
    
    @staticmethod
    async def get_image(
        db: AsyncSession,
        image_id: UUID,
        practice_id: UUID,
    ) -> Optional[PatientImage]:
        """Get an image"""
        result = await db.execute(
            select(PatientImage).where(
                PatientImage.id == image_id,
                PatientImage.practice_id == practice_id,
                PatientImage.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_public_image(
        db: AsyncSession,
        image_id: UUID,
        token: str,
    ) -> Optional[PatientImage]:
        """Get image by public share token"""
        result = await db.execute(
            select(PatientImage).where(
                PatientImage.id == image_id,
                PatientImage.share_token == token,
                PatientImage.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_image(
        db: AsyncSession,
        practice_id: UUID,
        patient_id: UUID,
        provider_id: UUID,
        image_type: ImageType,
        file_path: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        **kwargs
    ) -> PatientImage:
        """Create an image record"""
        image = PatientImage(
            practice_id=practice_id,
            patient_id=patient_id,
            provider_id=provider_id,
            image_type=image_type,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            acquisition_date=datetime.now(),
            **kwargs
        )
        db.add(image)
        await db.commit()
        await db.refresh(image)
        logger.info(f"Created image record: {image.id}")
        return image
    
    @staticmethod
    async def update_image(
        db: AsyncSession,
        image_id: UUID,
        **kwargs
    ) -> Optional[PatientImage]:
        """Update image metadata"""
        result = await db.execute(
            select(PatientImage).where(PatientImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        
        if not image:
            return None
        
        for key, value in kwargs.items():
            if hasattr(image, key):
                setattr(image, key, value)
        
        await db.commit()
        await db.refresh(image)
        logger.info(f"Updated image: {image_id}")
        return image
    
    @staticmethod
    async def delete_image(
        db: AsyncSession,
        image_id: UUID,
    ) -> bool:
        """Soft delete an image"""
        result = await db.execute(
            select(PatientImage).where(PatientImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        
        if not image:
            return False
        
        image.is_deleted = True
        image.deleted_at = datetime.now()
        await db.commit()
        logger.info(f"Deleted image: {image_id}")
        return True
    
    @staticmethod
    async def add_annotations(
        db: AsyncSession,
        image_id: UUID,
        annotations: List[Dict[str, Any]],
    ) -> Optional[PatientImage]:
        """Add annotations to image"""
        result = await db.execute(
            select(PatientImage).where(PatientImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        
        if not image:
            return None
        
        # Convert annotations to JSON string
        annotations_json = json.dumps(annotations)
        image.annotations = annotations_json
        
        await db.commit()
        await db.refresh(image)
        logger.info(f"Added annotations to image: {image_id}")
        return image
    
    @staticmethod
    async def get_image_series(
        db: AsyncSession,
        patient_id: UUID,
        practice_id: UUID,
    ) -> List[ImageSeries]:
        """Get image series for patient"""
        query = select(ImageSeries).where(
            ImageSeries.patient_id == patient_id,
            ImageSeries.practice_id == practice_id,
        ).order_by(ImageSeries.acquisition_date.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_series(
        db: AsyncSession,
        series_id: UUID,
        practice_id: UUID,
    ) -> Optional[ImageSeries]:
        """Get a series"""
        result = await db.execute(
            select(ImageSeries).where(
                ImageSeries.id == series_id,
                ImageSeries.practice_id == practice_id,
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_series(
        db: AsyncSession,
        practice_id: UUID,
        patient_id: UUID,
        provider_id: UUID,
        **kwargs
    ) -> ImageSeries:
        """Create an image series"""
        series = ImageSeries(
            practice_id=practice_id,
            patient_id=patient_id,
            provider_id=provider_id,
            **kwargs
        )
        db.add(series)
        await db.commit()
        await db.refresh(series)
        logger.info(f"Created image series: {series.id}")
        return series
    
    @staticmethod
    async def update_series(
        db: AsyncSession,
        series_id: UUID,
        **kwargs
    ) -> Optional[ImageSeries]:
        """Update image series"""
        result = await db.execute(
            select(ImageSeries).where(ImageSeries.id == series_id)
        )
        series = result.scalar_one_or_none()
        
        if not series:
            return None
        
        for key, value in kwargs.items():
            if hasattr(series, key):
                setattr(series, key, value)
        
        await db.commit()
        await db.refresh(series)
        logger.info(f"Updated image series: {series_id}")
        return series
    
    @staticmethod
    async def get_templates(
        db: AsyncSession,
        practice_id: UUID,
        is_active: Optional[bool] = None,
    ) -> List[ImageTemplate]:
        """Get image templates"""
        query = select(ImageTemplate).where(
            ImageTemplate.practice_id == practice_id
        )
        
        if is_active is not None:
            query = query.where(ImageTemplate.is_active == is_active)
        
        query = query.order_by(ImageTemplate.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_template(
        db: AsyncSession,
        template_id: UUID,
        practice_id: UUID,
    ) -> Optional[ImageTemplate]:
        """Get a template"""
        result = await db.execute(
            select(ImageTemplate).where(
                ImageTemplate.id == template_id,
                ImageTemplate.practice_id == practice_id,
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_template(
        db: AsyncSession,
        practice_id: UUID,
        name: str,
        configuration: List[Dict[str, Any]],
        **kwargs
    ) -> ImageTemplate:
        """Create an image template"""
        # Convert configuration to JSON string
        configuration_json = json.dumps(configuration)
        
        template = ImageTemplate(
            practice_id=practice_id,
            name=name,
            configuration=configuration_json,
            **kwargs
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        logger.info(f"Created image template: {template.id}")
        return template
    
    @staticmethod
    async def update_template(
        db: AsyncSession,
        template_id: UUID,
        **kwargs
    ) -> Optional[ImageTemplate]:
        """Update image template"""
        result = await db.execute(
            select(ImageTemplate).where(ImageTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        # Handle configuration conversion
        if 'configuration' in kwargs and kwargs['configuration']:
            configuration_json = json.dumps(kwargs['configuration'])
            kwargs['configuration'] = configuration_json
        
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        await db.commit()
        await db.refresh(template)
        logger.info(f"Updated image template: {template_id}")
        return template
