"""
File Upload Validation
Validates file uploads for security
"""

import magic
import re
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from typing import Tuple

# Allowed MIME types for uploads
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'application/pdf',
    'application/dicom',  # Medical imaging
}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


async def validate_upload_file(file: UploadFile) -> Tuple[bool, str]:
    """
    Validate uploaded file for security
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        Tuple of (is_valid, result_message_or_safe_filename)
    """
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE // 1024 // 1024}MB"
    
    if size == 0:
        return False, "File is empty"
    
    # Read first chunk for magic number detection
    chunk = await file.read(2048)
    await file.seek(0)  # Reset file pointer
    
    # Detect actual file type using magic numbers (not just extension)
    mime = magic.from_buffer(chunk, mime=True)
    
    if mime not in ALLOWED_MIME_TYPES:
        return False, f"File type not allowed: {mime}"
    
    # Validate filename for path traversal
    if not file.filename:
        return False, "Filename is required"
    
    safe_filename = Path(file.filename).name
    if safe_filename != file.filename:
        return False, "Invalid filename (path traversal detected)"
    
    # Sanitize filename - remove special characters
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', safe_filename)
    
    # Ensure filename has extension
    if '.' not in safe_filename:
        return False, "Filename must have an extension"
    
    return True, safe_filename
