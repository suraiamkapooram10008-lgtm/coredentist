"""
AWS S3 File Storage Service
Handles file uploads, downloads, and management
"""

import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class S3StorageService:
    """AWS S3 storage service for file management"""
    
    def __init__(self):
        """Initialize S3 client"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.cloudfront_domain = settings.AWS_CLOUDFRONT_DOMAIN
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        folder: str = "uploads",
        patient_id: Optional[str] = None,
        user_id: Optional[str] = None,
        skip_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Upload a file to S3 with comprehensive security validation
        
        Args:
            file_content: Binary content of the file
            filename: Original filename
            content_type: MIME type of the file
            folder: Folder path in S3 bucket
            patient_id: Optional patient ID for organization
            user_id: Optional user ID for tracking
            skip_validation: Skip security validation (use with caution)
        
        Returns:
            Dictionary with file URL and metadata
        """
        try:
            # SECURITY FIX: Validate file before upload
            if not skip_validation:
                from app.core.file_security import validate_file_upload, FileSecurityError
                
                try:
                    validation_result = validate_file_upload(
                        file_content=file_content,
                        filename=filename
                    )
                    
                    # Use secure filename
                    unique_filename = validation_result['secure_filename']
                    content_type = validation_result['mime_type']  # Use detected MIME type
                    file_hash = validation_result['hash']
                    
                    logger.info(
                        f"File validation passed: {filename} -> {unique_filename}",
                        extra={
                            "original": filename,
                            "secure": unique_filename,
                            "size": validation_result['size'],
                            "hash": file_hash[:16] + "..."
                        }
                    )
                    
                except FileSecurityError as e:
                    logger.error(f"File validation failed: {e}")
                    return {
                        "success": False,
                        "error": f"File validation failed: {str(e)}"
                    }
            else:
                # Legacy path: generate unique filename without validation
                file_extension = os.path.splitext(filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{file_extension}"
                file_hash = None
            
            # Build S3 key path
            s3_key = f"{folder}"
            if patient_id:
                s3_key += f"/patient-{patient_id}"
            if user_id:
                s3_key += f"/user-{user_id}"
            s3_key += f"/{unique_filename}"
            
            # Prepare metadata
            metadata = {
                'original_filename': filename,
                'uploaded_at': datetime.utcnow().isoformat()
            }
            if file_hash:
                metadata['sha256_hash'] = file_hash
            
            # Upload to S3 with security headers
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata=metadata,
                # SECURITY: Prevent inline execution of uploaded files
                ContentDisposition='attachment',
                # SECURITY: Set cache control
                CacheControl='max-age=31536000',
                # SECURITY: Server-side encryption
                ServerSideEncryption='AES256'
            )
            
            # Generate file URL
            file_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            if self.cloudfront_domain:
                file_url = f"https://{self.cloudfront_domain}/{s3_key}"
            
            logger.info(f"File uploaded successfully: {s3_key}")
            
            return {
                "success": True,
                "file_url": file_url,
                "s3_key": s3_key,
                "filename": filename,
                "secure_filename": unique_filename,
                "content_type": content_type,
                "size": len(file_content),
                "hash": file_hash
            }
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def download_file(self, s3_key: str) -> Optional[bytes]:
        """
        Download a file from S3
        
        Args:
            s3_key: S3 object key
        
        Returns:
            File content as bytes, or None if error
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"S3 download error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return None
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for temporary file access
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL string, or None if error
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3
        
        Args:
            s3_key: S3 object key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"File deleted: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during delete: {e}")
            return False
    
    def list_files(
        self,
        prefix: str = "",
        max_keys: int = 100
    ) -> list:
        """
        List files in S3 bucket
        
        Args:
            prefix: Prefix to filter files
            max_keys: Maximum number of files to return
        
        Returns:
            List of file metadata dictionaries
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag']
                    })
            
            return files
            
        except ClientError as e:
            logger.error(f"S3 list error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during list: {e}")
            return []
    
    def get_file_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific file
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Dictionary with file metadata, or None if error
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified').isoformat(),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"S3 metadata error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

# Singleton instance
s3_storage = S3StorageService()