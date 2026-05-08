"""
CoreDent API - Main Application Entry Point
FastAPI application with HIPAA-compliant security features
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config_simple import settings
from app.core.database import engine
from app.core.limiter import limiter
from app.api.v1.api import api_router
from app.models import Base

import logging
import logging.config
import json
import re
import traceback
from datetime import datetime
from pythonjsonlogger import jsonlogger
from typing import Any, Dict

if settings.ENVIRONMENT == "production":
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, record, message, extra):
            super().add_fields(record, message, extra)
            from datetime import timezone
            record['timestamp'] = datetime.now(timezone.utc).isoformat()
            record['level'] = record.levelname
            record['service'] = settings.APP_NAME
    
    handler = logging.StreamHandler()
    handler.setFormatter(CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s'))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]

logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking and monitoring (SECURITY FIX)
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
except Exception:
    sentry_sdk = None

if settings.SENTRY_DSN and sentry_sdk:
    try:
        # SECURITY FIX: Enhanced Sentry configuration with security event tracking
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )
        
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                sentry_logging,
            ],
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            profiles_sample_rate=0.1,  # 10% for profiling
            environment=settings.ENVIRONMENT,
            release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
            
            # SECURITY: Filter sensitive data from error reports
            before_send=lambda event, hint: filter_sensitive_data(event),
            
            # SECURITY: Track security-relevant events
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send PII by default
        )
        
        logger.info("Sentry monitoring initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")
        sentry_sdk = None
else:
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured - monitoring disabled")


def filter_sensitive_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter sensitive data from Sentry events (HIPAA compliance)
    
    Removes:
    - Passwords
    - Tokens
    - API keys
    - Patient data
    - Email addresses
    - Phone numbers
    """
    sensitive_keys = [
        'password', 'token', 'secret', 'api_key', 'authorization',
        'ssn', 'social_security', 'credit_card', 'card_number',
        'patient_name', 'email', 'phone', 'address'
    ]
    
    def redact_dict(d: dict) -> dict:
        """Recursively redact sensitive keys"""
        if not isinstance(d, dict):
            return d
        
        for key in list(d.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                d[key] = '[REDACTED]'
            elif isinstance(d[key], dict):
                d[key] = redact_dict(d[key])
            elif isinstance(d[key], list):
                d[key] = [redact_dict(item) if isinstance(item, dict) else item for item in d[key]]
        
        return d
    
    # Redact request data
    if 'request' in event:
        event['request'] = redact_dict(event['request'])
    
    # Redact extra data
    if 'extra' in event:
        event['extra'] = redact_dict(event['extra'])
    
    return event


def log_security_event(
    event_type: str,
    severity: str,
    message: str,
    extra: Dict[str, Any] = None
):
    """
    Log security events to Sentry and application logs
    
    Args:
        event_type: Type of security event (e.g., 'rate_limit', 'auth_failure')
        severity: Severity level ('info', 'warning', 'error', 'critical')
        message: Event description
        extra: Additional context data
    """
    log_data = {
        'event_type': event_type,
        'severity': severity,
        'timestamp': datetime.now().isoformat(),
        **(extra or {})
    }
    
    # Log to application logs
    if severity == 'critical':
        logger.critical(message, extra=log_data)
    elif severity == 'error':
        logger.error(message, extra=log_data)
    elif severity == 'warning':
        logger.warning(message, extra=log_data)
    else:
        logger.info(message, extra=log_data)
    
    # Send to Sentry if configured
    if sentry_sdk:
        with sentry_sdk.push_scope() as scope:
            scope.set_tag('event_type', event_type)
            scope.set_tag('severity', severity)
            scope.set_context('security_event', log_data)
            
            if severity in ['error', 'critical']:
                sentry_sdk.capture_message(message, level=severity)
            else:
                sentry_sdk.add_breadcrumb(
                    category='security',
                    message=message,
                    level=severity,
                    data=log_data
                )

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="HIPAA-compliant Dental Practice Management System API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Initialize rate limiter with default limits
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security headers in production (Railway handles HTTPS at proxy level)
if not settings.DEBUG:
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        # HSTS (Railway already provides HTTPS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        # SECURITY FIX: Add comprehensive security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # NEW: Content Security Policy to prevent XSS and exfiltration
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https://public.blob.vercel-storage.com; "
            "connect-src 'self' https://sentry.io;"
        )
        return response

# CORS Middleware - Restrict to specific methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods only
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-CSRF-Token",
        "X-Requested-With",
    ],  # Explicit headers only
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
    max_age=3600,  # Cache preflight for 1 hour
)

# SECURITY FIX: Security Monitoring Middleware
@app.middleware("http")
async def security_monitoring_middleware(request: Request, call_next):
    """
    Monitor and log security-relevant events
    
    Tracks:
    - Failed authentication attempts
    - Rate limit violations
    - Suspicious request patterns
    - Error rates
    """
    import time
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Track failed authentication
        if response.status_code == 401:
            log_security_event(
                event_type='auth_failure',
                severity='warning',
                message=f"Authentication failed: {request.url.path}",
                extra={
                    'path': str(request.url.path),
                    'method': request.method,
                    'ip': request.client.host if request.client else 'unknown',
                    'user_agent': request.headers.get('user-agent', 'unknown')
                }
            )
        
        # Track rate limit violations
        elif response.status_code == 429:
            log_security_event(
                event_type='rate_limit',
                severity='warning',
                message=f"Rate limit exceeded: {request.url.path}",
                extra={
                    'path': str(request.url.path),
                    'method': request.method,
                    'ip': request.client.host if request.client else 'unknown'
                }
            )
        
        # Track server errors
        elif response.status_code >= 500:
            log_security_event(
                event_type='server_error',
                severity='error',
                message=f"Server error: {request.url.path}",
                extra={
                    'path': str(request.url.path),
                    'method': request.method,
                    'status_code': response.status_code,
                    'duration_ms': (time.time() - start_time) * 1000
                }
            )
        
        return response
        
    except Exception as e:
        # Log unexpected errors
        log_security_event(
            event_type='exception',
            severity='critical',
            message=f"Unhandled exception: {str(e)}",
            extra={
                'path': str(request.url.path),
                'method': request.method,
                'error': str(e)
            }
        )
        raise

# HIGH-01 FIX: Audit Logging Middleware for HIPAA compliance
if settings.AUDIT_LOG_ENABLED:
    @app.middleware("http")
    async def audit_logging_middleware(request: Request, call_next):
        """Log all API requests for HIPAA audit trail"""
        import time
        from datetime import datetime, timezone
        
        start_time = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Only log API requests (not health checks, metrics, docs)
        if request.url.path.startswith("/api/"):
            # Get user info if authenticated
            user_id = None
            practice_id = None
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                try:
                    from app.core.security import decode_token
                    token = auth_header[7:]
                    payload = decode_token(token)
                    if payload:
                        user_id = payload.get("sub")
                        practice_id = payload.get("practice_id")
                except Exception:
                    pass
            
            # Log the request
            logger.info(
                "API_REQUEST",
                extra={
                    "audit": True,
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.query_params) if request.query_params else None,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "practice_id": practice_id,
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        
        return response

# Redis-backed rate limiting (if REDIS_URL is configured)
if settings.REDIS_URL:
    try:
        from app.core.redis_rate_limit import RedisRateLimitMiddleware
        app.add_middleware(RedisRateLimitMiddleware, requests=settings.RATE_LIMIT_PER_MINUTE)
        print("✅ Redis rate limiting enabled")
    except Exception as e:
        print(f"⚠️  Redis rate limiting unavailable: {e}")

# Trusted Host Middleware (security)
# Only enable if ALLOWED_HOSTS is explicitly configured
if not settings.DEBUG and settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors - hide details in production"""
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.errors(),
                "body": exc.body,
            },
        )
    
    # Production: Don't expose internal details
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "type": "validation_error",
        },
    )


# PHI Scrubbing Patterns (Expanded for clinical coverage)
PHI_KEYS = {
    "first_name", "last_name", "email", "phone", "dob", "address", 
    "ssn", "insurance_id", "license", "account_number", "card_number"
}

def redact_phi(data: Any) -> Any:
    """Recursively scrub common PHI patterns from a dictionary or list."""
    if isinstance(data, dict):
        return {
            k: "[REDACTED]" if k.lower() in PHI_KEYS else redact_phi(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [redact_phi(item) for item in data]
    return data

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors - never expose details in production + scrub PHI from logs."""
    
    # Scrub PHI from request info for internal logging
    client_host = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    url = str(request.url)
    
    # Redact URL if it contains PHI patterns (e.g. patients?name=John)
    for key in PHI_KEYS:
        url = re.sub(rf"({key}=)[^&]*", r"\1[REDACTED]", url, flags=re.IGNORECASE)
    
    # Try to scrub the request body if it's JSON
    body_display = "[NOT_JSON_OR_NOT_LOADED]"
    try:
        # Note: Be careful with large bodies, but for PHI fields we usually have JSON
        body = await request.json()
        body_display = str(redact_phi(body))
    except Exception:
        pass

    # Log full error internally with SANITIZED request context
    logger.error(
        f"Unhandled exception: {method} {url} from {client_host}\n"
        f"Body: {body_display}\n"
        f"Error: {str(exc)}\n"
        f"Traceback: {traceback.format_exc()}",
        extra={
            "path": path,
            "method": method,
            "client": client_host,
        }
    )
    
    # In debug mode, raise for detailed traceback
    if settings.DEBUG:
        raise exc
    
    # In production, return generic error (never expose internals)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal error occurred. Please contact support if the problem persists.",
            "type": "server_error",
        },
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create database tables (in production, use Alembic migrations)
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    if settings.DEBUG:
        print(f"📚 API Docs: http://localhost:3000/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print(f"👋 {settings.APP_NAME} shutting down")


# HIGH-03 FIX: Health check endpoint - minimal info for monitoring, detailed info requires auth
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring - returns minimal info for security"""
    db_status = "unknown"
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    # Return minimal info for security (no version, no app name in production)
    if settings.DEBUG:
        return {
            "status": "healthy" if db_status == "connected" else "degraded",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": db_status,
        }
    
    # Production: minimal response
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
    }


# CRIT-04 FIX: Metrics endpoint protected - only accessible in debug mode or with secret key
@app.get("/metrics", tags=["Monitoring"])
async def metrics(request: Request):
    """Prometheus metrics endpoint - PROTECTED"""
    # In production, only allow access if a secret monitoring token is provided
    if not settings.DEBUG:
        monitoring_token = request.query_params.get("token")
        secret_token = request.headers.get("X-Monitoring-Token")
        
        # Allow access only with valid token (set via env var MONITORING_TOKEN)
        expected_token = settings.MONITORING_TOKEN
        if not expected_token or (monitoring_token != expected_token and secret_token != expected_token):
            from fastapi import HTTPException as HTTPExc
            raise HTTPExc(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Monitoring endpoint requires authentication.",
            )
    
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    return PlainTextResponse(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=3000,
        reload=settings.DEBUG,
        log_level="info",
    )
