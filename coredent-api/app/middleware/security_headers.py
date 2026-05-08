"""
Security Headers Middleware
Add security headers to all responses. CSP is always applied regardless of DEBUG mode.
Includes nonce-based CSP for production XSS protection.
"""

import secrets
from fastapi import Request
from app.core.config_simple import settings


async def security_headers_middleware(request: Request, call_next):
    """Add comprehensive security headers to all responses"""
    
    # Generate nonce for this request (used in CSP for production)
    nonce = secrets.token_urlsafe(24)
    request.state.nonce = nonce
    
    response = await call_next(request)

    # Always apply security headers - CSP is critical even in dev
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # Add request ID for tracing (REC-07)
    import uuid
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response.headers["X-Request-ID"] = request_id
    
    # Set CSP based on environment
    # Production uses nonce-based CSP, development uses unsafe-inline for React HMR
    if settings.ENVIRONMENT == "production" or not settings.DEBUG:
        # Production CSP with nonces - more secure, blocks inline scripts
        # Note: React must be configured to use nonces (see docs/CSP_FIX_GUIDE.md)
        response.headers["Content-Security-Policy"] = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' 'strict-dynamic' https://cdn.jsdelivr.net https://js.stripe.com https://api.razorpay.com; "
            f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline' https://fonts.googleapis.com; "
            f"font-src 'self' https://fonts.gstatic.com data:; "
            f"img-src 'self' data: https: blob:; "
            f"connect-src 'self' https://sentry.io https://api.stripe.com https://api.razorpay.com; "
            f"frame-src 'self' https://js.stripe.com https://api.razorpay.com; "
            f"object-src 'none'; "
            f"base-uri 'self'; "
            f"form-action 'self';"
        )
    else:
        # Development CSP - allows unsafe-inline for React HMR
        # WARNING: This weakens XSS protection, only use in development!
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://js.stripe.com https://api.razorpay.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' ws://localhost:* http://localhost:* https://sentry.io https://api.stripe.com https://api.razorpay.com; "
            "frame-src 'self' https://js.stripe.com https://api.razorpay.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

    # Expose nonce to frontend via header (for React to read if needed)
    if settings.ENVIRONMENT == "production":
        response.headers["X-CSP-Nonce"] = nonce

    # HSTS only in production (to avoid issues with local dev over HTTP)
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    return response