"""
CoreDent API - Main Application Entry Point
FastAPI application with HIPAA-compliant security features
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine
from app.api.v1.api import api_router
from app.models import Base

import logging
import logging.config
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger

if settings.ENVIRONMENT == "production":
    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, record, message, extra):
            super().add_fields(record, message, extra)
            record['timestamp'] = datetime.utcnow().isoformat()
            record['level'] = record.levelname
            record['service'] = settings.APP_NAME
    
    handler = logging.StreamHandler()
    handler.setFormatter(CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s'))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]

logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking (optional)
# Sentry is optional for local development and tests; some environments (e.g., Python 3.13)
# may have compatibility issues with dependencies like eventlet.
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
except Exception:
    sentry_sdk = None

if settings.SENTRY_DSN and sentry_sdk:
    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            environment=settings.ENVIRONMENT,
        )
    except Exception:
        # Fail gracefully if Sentry initialization fails
        sentry_sdk = None

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
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])
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


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors - never expose details in production"""
    
    # Log full error internally with request context
    import logging
    logger = logging.getLogger(__name__)
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None,
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


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    db_status = "unknown"
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
    }


# Prometheus metrics endpoint
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
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
