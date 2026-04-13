"""
CAPTCHA Verification Module
Supports reCAPTCHA v3 for bot protection
"""

import logging
import httpx
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class CaptchaVerificationError(Exception):
    """Raised when CAPTCHA verification fails"""
    pass


async def verify_recaptcha_v3(
    token: str,
    action: str = "booking",
    min_score: float = 0.5
) -> bool:
    """
    Verify reCAPTCHA v3 token
    
    Args:
        token: reCAPTCHA token from frontend
        action: Expected action name
        min_score: Minimum score (0.0-1.0, default 0.5)
        
    Returns:
        True if verification passes
        
    Raises:
        CaptchaVerificationError: If verification fails
    """
    if not settings.RECAPTCHA_SECRET_KEY:
        logger.warning("reCAPTCHA not configured, skipping verification")
        return True  # Allow in development
    
    if not token:
        raise CaptchaVerificationError("CAPTCHA token is required")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": settings.RECAPTCHA_SECRET_KEY,
                    "response": token,
                },
                timeout=5.0
            )
            
            result = response.json()
            
            if not result.get("success"):
                error_codes = result.get("error-codes", [])
                logger.error(f"reCAPTCHA verification failed: {error_codes}")
                raise CaptchaVerificationError(f"CAPTCHA verification failed: {error_codes}")
            
            # Verify action matches
            if result.get("action") != action:
                logger.error(
                    f"reCAPTCHA action mismatch: expected {action}, got {result.get('action')}"
                )
                raise CaptchaVerificationError("CAPTCHA action mismatch")
            
            # Verify score meets minimum
            score = result.get("score", 0.0)
            if score < min_score:
                logger.warning(
                    f"reCAPTCHA score too low: {score} < {min_score}",
                    extra={"score": score, "min_score": min_score}
                )
                raise CaptchaVerificationError(f"CAPTCHA score too low: {score}")
            
            logger.info(f"reCAPTCHA verification successful: score={score}")
            return True
            
    except httpx.TimeoutException:
        logger.error("reCAPTCHA verification timeout")
        raise CaptchaVerificationError("CAPTCHA verification timeout")
    except httpx.HTTPError as e:
        logger.error(f"reCAPTCHA HTTP error: {e}")
        raise CaptchaVerificationError("CAPTCHA verification error")
    except Exception as e:
        logger.error(f"Unexpected reCAPTCHA error: {e}")
        raise CaptchaVerificationError("CAPTCHA verification error")


async def verify_hcaptcha(
    token: str,
    remote_ip: Optional[str] = None
) -> bool:
    """
    Verify hCaptcha token (alternative to reCAPTCHA)
    
    Args:
        token: hCaptcha token from frontend
        remote_ip: Client IP address (optional)
        
    Returns:
        True if verification passes
        
    Raises:
        CaptchaVerificationError: If verification fails
    """
    if not settings.HCAPTCHA_SECRET_KEY:
        logger.warning("hCaptcha not configured, skipping verification")
        return True  # Allow in development
    
    if not token:
        raise CaptchaVerificationError("CAPTCHA token is required")
    
    try:
        async with httpx.AsyncClient() as client:
            data = {
                "secret": settings.HCAPTCHA_SECRET_KEY,
                "response": token,
            }
            if remote_ip:
                data["remoteip"] = remote_ip
            
            response = await client.post(
                "https://hcaptcha.com/siteverify",
                data=data,
                timeout=5.0
            )
            
            result = response.json()
            
            if not result.get("success"):
                error_codes = result.get("error-codes", [])
                logger.error(f"hCaptcha verification failed: {error_codes}")
                raise CaptchaVerificationError(f"CAPTCHA verification failed: {error_codes}")
            
            logger.info("hCaptcha verification successful")
            return True
            
    except httpx.TimeoutException:
        logger.error("hCaptcha verification timeout")
        raise CaptchaVerificationError("CAPTCHA verification timeout")
    except httpx.HTTPError as e:
        logger.error(f"hCaptcha HTTP error: {e}")
        raise CaptchaVerificationError("CAPTCHA verification error")
    except Exception as e:
        logger.error(f"Unexpected hCaptcha error: {e}")
        raise CaptchaVerificationError("CAPTCHA verification error")
