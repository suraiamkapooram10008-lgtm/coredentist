"""
Webhook Security Module
Enhanced security for webhook endpoints (Stripe, etc.)
"""

import hashlib
import hmac
import logging
from typing import Optional, List
from fastapi import Request, HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

# Stripe webhook IPs (as of 2024 - update regularly)
# Source: https://stripe.com/docs/ips
STRIPE_WEBHOOK_IPS = [
    "3.18.12.63",
    "3.130.192.231",
    "13.235.14.237",
    "13.235.122.149",
    "18.211.135.69",
    "35.154.171.200",
    "52.15.183.38",
    "54.88.130.119",
    "54.88.130.237",
    "54.187.174.169",
    "54.187.205.235",
    "54.187.216.72",
]


class WebhookSecurityError(Exception):
    """Raised when webhook security validation fails"""
    pass


def verify_ip_whitelist(request: Request, allowed_ips: List[str]) -> bool:
    """
    Verify request comes from whitelisted IP
    
    Args:
        request: FastAPI request object
        allowed_ips: List of allowed IP addresses
        
    Returns:
        True if IP is whitelisted
        
    Raises:
        WebhookSecurityError: If IP is not whitelisted
    """
    client_ip = request.client.host if request.client else None
    
    # Check X-Forwarded-For header (for proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        client_ip = forwarded_for.split(",")[0].strip()
    
    if not client_ip:
        logger.error("Unable to determine client IP for webhook request")
        raise WebhookSecurityError("Unable to determine client IP")
    
    if client_ip not in allowed_ips:
        logger.error(
            f"Webhook request from unauthorized IP: {client_ip}",
            extra={"client_ip": client_ip, "allowed_ips": allowed_ips}
        )
        raise WebhookSecurityError(f"Unauthorized IP: {client_ip}")
    
    logger.info(f"Webhook request from whitelisted IP: {client_ip}")
    return True


def verify_hmac_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify HMAC signature for additional webhook security
    
    Args:
        payload: Raw request body
        signature: Signature from request header
        secret: Shared secret key
        algorithm: Hash algorithm (default: sha256)
        
    Returns:
        True if signature is valid
        
    Raises:
        WebhookSecurityError: If signature is invalid
    """
    if not secret:
        logger.error("HMAC secret not configured")
        raise WebhookSecurityError("HMAC secret not configured")
    
    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(signature, expected_signature):
        logger.error(
            "HMAC signature verification failed",
            extra={"expected": expected_signature[:10] + "...", "received": signature[:10] + "..."}
        )
        raise WebhookSecurityError("Invalid HMAC signature")
    
    logger.info("HMAC signature verified successfully")
    return True


async def verify_stripe_webhook_security(request: Request) -> bool:
    """
    Comprehensive Stripe webhook security verification
    
    Performs:
    1. IP whitelist check
    2. Stripe signature verification (existing)
    3. Additional HMAC verification (optional)
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if all security checks pass
        
    Raises:
        HTTPException: If any security check fails
    """
    try:
        # 1. Verify IP whitelist
        if settings.STRIPE_WEBHOOK_IP_WHITELIST_ENABLED:
            verify_ip_whitelist(request, STRIPE_WEBHOOK_IPS)
        
        # 2. Stripe signature verification happens in endpoint
        # (using stripe.Webhook.construct_event)
        
        # 3. Additional HMAC verification (optional layer)
        if settings.STRIPE_WEBHOOK_HMAC_SECRET:
            payload = await request.body()
            hmac_signature = request.headers.get("X-Webhook-HMAC")
            
            if hmac_signature:
                verify_hmac_signature(
                    payload,
                    hmac_signature,
                    settings.STRIPE_WEBHOOK_HMAC_SECRET
                )
        
        return True
        
    except WebhookSecurityError as e:
        logger.error(f"Webhook security check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook security verification failed"
        )
    except Exception as e:
        logger.error(f"Unexpected error in webhook security: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def log_webhook_attempt(
    request: Request,
    webhook_type: str,
    success: bool,
    error: Optional[str] = None
):
    """
    Log all webhook attempts for security monitoring
    
    Args:
        request: FastAPI request object
        webhook_type: Type of webhook (stripe, paypal, etc.)
        success: Whether webhook processing succeeded
        error: Error message if failed
    """
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("X-Forwarded-For", "none")
    user_agent = request.headers.get("User-Agent", "none")
    
    log_data = {
        "webhook_type": webhook_type,
        "success": success,
        "client_ip": client_ip,
        "forwarded_for": forwarded_for,
        "user_agent": user_agent,
        "error": error,
    }
    
    if success:
        logger.info(f"Webhook processed successfully: {webhook_type}", extra=log_data)
    else:
        logger.error(f"Webhook processing failed: {webhook_type}", extra=log_data)
