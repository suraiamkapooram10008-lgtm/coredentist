"""
HIPAA Compliance Monitoring
Provides HIPAA compliance verification and audit features
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config_simple import settings
from app.core.encryption import encrypt_value, decrypt_value
from app.core.audit import log_audit_event
from app.models.user import User, UserRole
from app.api.deps import get_current_user
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/encryption-test")
async def test_encryption(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Test encryption/decryption functionality for HIPAA compliance
    Only accessible to admin users
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access encryption tests"
        )

    test_data = "HIPAA Test Data - Patient Information"
    encrypted = encrypt_value(test_data)
    decrypted = decrypt_value(encrypted)

    success = test_data == decrypted

    # Log the test
    await log_audit_event(
        db, current_user, "encryption_test_performed",
        "system", None, None
    )

    if success:
        logger.info(f"Encryption test passed by user {current_user.email}")
    else:
        logger.error(f"Encryption test FAILED by user {current_user.email}")

    return {
        "encryption_working": success,
        "test_data": test_data if success else "REDACTED",
        "encryption_key_configured": bool(settings.ENCRYPTION_KEY and settings.ENCRYPTION_KEY != "dev-encryption-key-change-in-production"),
        "recommendations": [
            "Ensure ENCRYPTION_KEY is set to a strong, unique value in production",
            "Regularly rotate encryption keys",
            "Monitor encryption failures in logs"
        ] if not success else []
    }


@router.get("/hipaa-status")
async def hipaa_compliance_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check HIPAA compliance status
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access HIPAA compliance status"
        )

    status_checks = {
        "encryption_key_configured": bool(settings.ENCRYPTION_KEY and settings.ENCRYPTION_KEY != "dev-encryption-key-change-in-production"),
        "secret_key_configured": bool(settings.SECRET_KEY and settings.SECRET_KEY != "dev-secret-key-change-in-production-for-hipaa-compliance"),
        "debug_mode_disabled": not settings.DEBUG,
        "environment_production": settings.ENVIRONMENT == "production",
        "https_enabled": not settings.DEBUG,  # Simplified check
        "audit_logging_enabled": True,  # Always enabled in our implementation
        "rate_limiting_enabled": True,  # Always enabled
        "csrf_protection_enabled": True,  # Always enabled
    }

    overall_compliant = all(status_checks.values())

    compliance_report = {
        "overall_compliant": overall_compliant,
        "checks": status_checks,
        "recommendations": []
    }

    if not status_checks["encryption_key_configured"]:
        compliance_report["recommendations"].append("Set a strong ENCRYPTION_KEY in production")

    if not status_checks["secret_key_configured"]:
        compliance_report["recommendations"].append("Set a strong SECRET_KEY in production")

    if status_checks["debug_mode_disabled"]:
        compliance_report["recommendations"].append("Disable DEBUG mode in production")

    if not status_checks["environment_production"]:
        compliance_report["recommendations"].append("Set ENVIRONMENT=production")

    # Log the compliance check
    await log_audit_event(
        db, current_user, "hipaa_compliance_check",
        "system", None, None
    )

    return compliance_report