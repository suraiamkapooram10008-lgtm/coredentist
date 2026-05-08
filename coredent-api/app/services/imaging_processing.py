"""
Imaging Processing Service
Handles image file processing, validation, and storage
"""

from typing import Optional, Tuple
from uuid import UUID
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.config_simple import settings
from app.utils.storage import storage
from app.models.imaging import PatientImage

logger = logging.getLogger(__name__)


class ImageFileProcessor:
    """Handles image file processing and validation"""
    
    # Allowed file types
    ALLOWED_MIME_TYPES = {
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
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf', '.tiff', '.tif'}
    
    @staticmethod
    async def validate_file(
        file: UploadFile,
    ) -> Tuple[bytes, str]:
        """Validate and read file"""
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise ValueError(
                f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )
        
        if file_size == 0:
            raise ValueError("File is empty")
        
        # Validate MIME type
        if file.content_type not in ImageFileProcessor.ALLOWED_MIME_TYPES:
            raise ValueError(
                f"File type '{file.content_type}' not allowed. "
                f"Allowed types: JPEG, PNG, GIF, BMP, WebP, PDF, TIFF"
            )
        
        # Validate file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ImageFileProcessor.ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension '{file_extension}' not allowed")
        
        logger.info(f"File validation passed: {file.filename} ({file_size} bytes)")
        return content, file_extension
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent security issues"""
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.() ')
        safe_filename = ''.join(c if c in safe_chars else '_' for c in filename)
        logger.debug(f"Sanitized filename: {filename} -> {safe_filename}")
        return safe_filename
    
    @staticmethod
    def generate_unique_filename(
        patient_id: UUID,
        file_extension: str,
    ) -> str:
        """Generate unique filename for storage"""
        unique_id = secrets.token_hex(8)
        filename = f"{patient_id}/{unique_id}{file_extension}"
        logger.debug(f"Generated unique filename: {filename}")
        return filename
    
    @staticmethod
    async def upload_file(
        content: bytes,
        unique_filename: str,
        mime_type: str,
    ) -> str:
        """Upload file to storage"""
        try:
            storage_path = storage.upload(content, unique_filename, mime_type)
            logger.info(f"File uploaded successfully: {storage_path}")
            return storage_path
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise
    
    @staticmethod
    def get_file_url(file_path: str) -> str:
        """Get URL for file"""
        try:
            url = storage.get_url(file_path)
            logger.debug(f"Generated URL for file: {file_path}")
            return url
        except Exception as e:
            logger.error(f"Failed to generate URL: {str(e)}")
            raise
    
    @staticmethod
    async def delete_file(file_path: str) -> bool:
        """Delete file from storage"""
        try:
            storage.delete(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False


class ImageSharingProcessor:
    """Handles image sharing and access control"""
    
    @staticmethod
    def generate_share_token() -> str:
        """Generate secure share token"""
        token = secrets.token_urlsafe(32)
        logger.debug("Generated share token")
        return token
    
    @staticmethod
    def generate_share_link(
        image_id: UUID,
        token: str,
    ) -> str:
        """Generate share link"""
        if not settings.FRONTEND_URL:
            raise ValueError("FRONTEND_URL not configured for image sharing")
        
        share_link = f"{settings.FRONTEND_URL}/viewer/{image_id}?token={token}"
        logger.debug(f"Generated share link for image: {image_id}")
        return share_link
    
    @staticmethod
    def get_share_expiry() -> datetime:
        """Get share link expiry time"""
        expiry = datetime.now(timezone.utc) + timedelta(days=30)
        logger.debug(f"Share link expires at: {expiry}")
        return expiry
    
    @staticmethod
    async def update_sharing_settings(
        db: AsyncSession,
        image: PatientImage,
        share_with_patient: bool,
        share_with_referral: bool,
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """Update image sharing settings"""
        image.is_shared_with_patient = share_with_patient
        image.is_shared_with_referral = share_with_referral
        
        share_link = None
        expires_at = None
        
        if share_with_patient or share_with_referral:
            # Generate new share token
            token = ImageSharingProcessor.generate_share_token()
            image.share_token = token
            
            # Generate share link
            share_link = ImageSharingProcessor.generate_share_link(image.id, token)
            expires_at = ImageSharingProcessor.get_share_expiry()
        
        await db.commit()
        logger.info(f"Updated sharing settings for image: {image.id}")
        
        return share_link, expires_at
    
    @staticmethod
    def verify_share_token(
        image: PatientImage,
        token: str,
    ) -> bool:
        """Verify share token"""
        if not image.share_token or image.share_token != token:
            logger.warning(f"Invalid share token for image: {image.id}")
            return False
        
        logger.debug(f"Share token verified for image: {image.id}")
        return True


class ImageMetadataProcessor:
    """Handles image metadata extraction and processing"""
    
    @staticmethod
    def extract_metadata(
        file_name: str,
        file_size: int,
        mime_type: str,
    ) -> dict:
        """Extract metadata from file"""
        metadata = {
            "file_name": file_name,
            "file_size": file_size,
            "mime_type": mime_type,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.debug(f"Extracted metadata: {metadata}")
        return metadata
    
    @staticmethod
    def get_file_extension_from_mime(mime_type: str) -> str:
        """Get file extension from MIME type"""
        mime_to_ext = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/webp': '.webp',
            'application/pdf': '.pdf',
            'image/tiff': '.tiff',
            'image/x-tiff': '.tiff',
        }
        return mime_to_ext.get(mime_type, '.bin')
    
    @staticmethod
    def get_mime_type_from_extension(extension: str) -> str:
        """Get MIME type from file extension"""
        ext_to_mime = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
        }
        return ext_to_mime.get(extension.lower(), 'application/octet-stream')
