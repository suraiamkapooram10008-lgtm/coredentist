"""
File Upload Security Module
Comprehensive security checks for file uploads
"""

import magic
import hashlib
import uuid
import re
import logging
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Magic number signatures for allowed file types
ALLOWED_MIME_TYPES = {
    # Images
    'image/jpeg': [b'\xFF\xD8\xFF'],
    'image/png': [b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'],
    'image/gif': [b'GIF87a', b'GIF89a'],
    'image/webp': [b'RIFF', b'WEBP'],
    
    # Documents
    'application/pdf': [b'%PDF-'],
    'application/msword': [b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'],  # DOC
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [
        b'PK\x03\x04'  # DOCX (ZIP-based)
    ],
    'text/plain': [],  # Text files don't have magic numbers
    
    # Archives (for batch uploads)
    'application/zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
}

# File size limits (in bytes)
FILE_SIZE_LIMITS = {
    'image/jpeg': 10 * 1024 * 1024,  # 10MB
    'image/png': 10 * 1024 * 1024,   # 10MB
    'image/gif': 5 * 1024 * 1024,    # 5MB
    'image/webp': 10 * 1024 * 1024,  # 10MB
    'application/pdf': 20 * 1024 * 1024,  # 20MB
    'application/msword': 10 * 1024 * 1024,  # 10MB
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 10 * 1024 * 1024,  # 10MB
    'text/plain': 1 * 1024 * 1024,  # 1MB
    'application/zip': 50 * 1024 * 1024,  # 50MB
}

# Default max size
DEFAULT_MAX_SIZE = 10 * 1024 * 1024  # 10MB


class FileSecurityError(Exception):
    """Raised when file security validation fails"""
    pass


def validate_file_extension(filename: str, allowed_extensions: list = None) -> bool:
    """
    Validate file extension
    
    Args:
        filename: Original filename
        allowed_extensions: List of allowed extensions (e.g., ['jpg', 'png'])
        
    Returns:
        True if extension is allowed
        
    Raises:
        FileSecurityError: If extension is not allowed
    """
    if allowed_extensions is None:
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'txt']
    
    # Extract extension
    ext = Path(filename).suffix.lower().lstrip('.')
    
    if not ext:
        raise FileSecurityError("File has no extension")
    
    if ext not in allowed_extensions:
        raise FileSecurityError(f"File extension '{ext}' is not allowed")
    
    return True


def validate_magic_number(file_content: bytes, expected_mime_type: str) -> bool:
    """
    Validate file magic number (file signature)
    
    This prevents attackers from uploading malicious files with fake extensions.
    
    Args:
        file_content: Binary content of the file
        expected_mime_type: Expected MIME type based on extension
        
    Returns:
        True if magic number matches expected type
        
    Raises:
        FileSecurityError: If magic number doesn't match
    """
    if expected_mime_type not in ALLOWED_MIME_TYPES:
        raise FileSecurityError(f"MIME type '{expected_mime_type}' is not allowed")
    
    # Get expected magic numbers
    magic_numbers = ALLOWED_MIME_TYPES[expected_mime_type]
    
    # Text files don't have magic numbers
    if not magic_numbers:
        return True
    
    # Check if file starts with any of the expected magic numbers
    for magic_num in magic_numbers:
        if file_content.startswith(magic_num):
            return True
    
    raise FileSecurityError(
        f"File content does not match expected type '{expected_mime_type}'. "
        "Possible file type mismatch or malicious upload attempt."
    )


def validate_file_size(file_content: bytes, mime_type: str) -> bool:
    """
    Validate file size is within limits
    
    Args:
        file_content: Binary content of the file
        mime_type: MIME type of the file
        
    Returns:
        True if size is within limits
        
    Raises:
        FileSecurityError: If file is too large
    """
    file_size = len(file_content)
    max_size = FILE_SIZE_LIMITS.get(mime_type, DEFAULT_MAX_SIZE)
    
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise FileSecurityError(
            f"File size ({file_size / (1024 * 1024):.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
        )
    
    if file_size == 0:
        raise FileSecurityError("File is empty")
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components (prevent directory traversal)
    filename = Path(filename).name
    
    # Remove or replace dangerous characters
    # Allow only alphanumeric, dash, underscore, dot
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Prevent multiple dots (can bypass extension checks)
    filename = re.sub(r'\.+', '.', filename)
    
    # Prevent leading/trailing dots or dashes
    filename = filename.strip('.-')
    
    # Limit filename length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


def generate_secure_filename(original_filename: str) -> str:
    """
    Generate a secure random filename while preserving extension
    
    Args:
        original_filename: Original filename
        
    Returns:
        Secure random filename with original extension
    """
    # Extract extension
    ext = Path(original_filename).suffix.lower()
    
    # Generate UUID-based filename
    secure_name = f"{uuid.uuid4().hex}{ext}"
    
    return secure_name


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content
    
    Useful for:
    - Duplicate detection
    - Integrity verification
    - Malware signature matching
    
    Args:
        file_content: Binary content of the file
        
    Returns:
        Hex-encoded SHA-256 hash
    """
    return hashlib.sha256(file_content).hexdigest()


def detect_mime_type(file_content: bytes, filename: str) -> str:
    """
    Detect MIME type using python-magic (libmagic)
    
    More reliable than trusting client-provided Content-Type header.
    
    Args:
        file_content: Binary content of the file
        filename: Original filename (for fallback)
        
    Returns:
        Detected MIME type
    """
    try:
        # Use python-magic to detect MIME type
        mime = magic.Magic(mime=True)
        detected_type = mime.from_buffer(file_content)
        return detected_type
    except Exception as e:
        logger.warning(f"Failed to detect MIME type with magic: {e}")
        
        # Fallback to extension-based detection
        ext = Path(filename).suffix.lower()
        extension_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.zip': 'application/zip',
        }
        return extension_map.get(ext, 'application/octet-stream')


def validate_file_upload(
    file_content: bytes,
    filename: str,
    allowed_extensions: list = None,
    max_size: int = None
) -> Dict[str, Any]:
    """
    Comprehensive file upload validation
    
    Performs all security checks:
    1. Extension validation
    2. File size validation
    3. MIME type detection
    4. Magic number validation
    5. Filename sanitization
    6. Hash calculation
    
    Args:
        file_content: Binary content of the file
        filename: Original filename
        allowed_extensions: List of allowed extensions
        max_size: Maximum file size in bytes (overrides default)
        
    Returns:
        Dictionary with validation results and metadata
        
    Raises:
        FileSecurityError: If any validation fails
    """
    try:
        # 1. Validate extension
        validate_file_extension(filename, allowed_extensions)
        
        # 2. Detect MIME type
        detected_mime = detect_mime_type(file_content, filename)
        
        # 3. Validate magic number
        validate_magic_number(file_content, detected_mime)
        
        # 4. Validate file size
        if max_size:
            if len(file_content) > max_size:
                raise FileSecurityError(f"File size exceeds maximum allowed size ({max_size} bytes)")
        else:
            validate_file_size(file_content, detected_mime)
        
        # 5. Sanitize filename
        safe_filename = sanitize_filename(filename)
        
        # 6. Generate secure filename
        secure_filename = generate_secure_filename(filename)
        
        # 7. Calculate file hash
        file_hash = calculate_file_hash(file_content)
        
        logger.info(
            f"File validation successful: {filename} -> {secure_filename}",
            extra={
                "original_filename": filename,
                "secure_filename": secure_filename,
                "mime_type": detected_mime,
                "size": len(file_content),
                "hash": file_hash[:16] + "..."
            }
        )
        
        return {
            "valid": True,
            "original_filename": filename,
            "safe_filename": safe_filename,
            "secure_filename": secure_filename,
            "mime_type": detected_mime,
            "size": len(file_content),
            "hash": file_hash,
        }
        
    except FileSecurityError as e:
        logger.warning(
            f"File validation failed: {filename}",
            extra={"filename": filename, "error": str(e)}
        )
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during file validation: {e}",
            extra={"filename": filename}
        )
        raise FileSecurityError(f"File validation error: {str(e)}")


# Optional: Virus scanning integration
async def scan_file_for_viruses(file_content: bytes, filename: str) -> bool:
    """
    Scan file for viruses using ClamAV or VirusTotal API
    
    NOTE: This requires additional setup:
    - ClamAV: Install clamd and python-clamd
    - VirusTotal: Get API key from virustotal.com
    
    Args:
        file_content: Binary content of the file
        filename: Original filename
        
    Returns:
        True if file is clean, False if infected
        
    Raises:
        FileSecurityError: If virus detected
    """
    # TODO: Implement virus scanning
    # Option 1: ClamAV (local, free, fast)
    # import clamd
    # cd = clamd.ClamdUnixSocket()
    # result = cd.scan_stream(file_content)
    
    # Option 2: VirusTotal API (cloud, requires API key, slower)
    # import requests
    # response = requests.post(
    #     'https://www.virustotal.com/api/v3/files',
    #     headers={'x-apikey': VIRUSTOTAL_API_KEY},
    #     files={'file': file_content}
    # )
    
    logger.info(f"Virus scanning not implemented for: {filename}")
    return True  # Assume clean if scanning not configured
