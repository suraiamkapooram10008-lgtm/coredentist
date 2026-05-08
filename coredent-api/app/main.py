"""
CoreDent API - Main Application Entry Point
FastAPI application with HIPAA-compliant security features
"""

import json
from decimal import Decimal
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config_simple import settings
from app.core.database import engine
from app.core.limiter import limiter
from app.core.logging_config import setup_logging
from app.core.sentry_config import init_sentry
from app.api.v1.api import api_router
from app.models import Base
from app.middleware.security_headers import security_headers_middleware
from app.middleware.security_monitoring import security_monitoring_middleware
from app.middleware.audit_logging import audit_logging_middleware
from app.exceptions.handlers import validation_exception_handler, general_exception_handler


# Custom JSON encoder for Decimal types
class DecimalJSONResponse(JSONResponse):
    """Custom JSONResponse that handles Decimal serialization"""
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=lambda obj: float(obj) if isinstance(obj, Decimal) else obj,
        ).encode("utf-8")


# Configure structured logging
setup_logging()

# Initialize Sentry for error tracking
init_sentry()

# Create FastAPI application with custom response class
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="HIPAA-compliant Dental Practice Management System API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    default_response_class=DecimalJSONResponse,  # Use custom JSON encoder
)

# Initialize rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Security headers middleware
if not settings.DEBUG:
    app.middleware("http")(security_headers_middleware)

# HTTPS enforcement middleware (production only)
if settings.ENVIRONMENT == "production":
    from app.middleware.https_enforcement import HTTPSEnforcementMiddleware
    app.add_middleware(HTTPSEnforcementMiddleware)

# Security monitoring middleware
app.middleware("http")(security_monitoring_middleware)

# Audit logging middleware
if settings.AUDIT_LOG_ENABLED:
    app.middleware("http")(audit_logging_middleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-CSRF-Token",
        "X-Requested-With",
    ],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
    max_age=3600,
)

# Redis-backed rate limiting (production-ready)
if settings.REDIS_URL:
    try:
        from app.core.redis_rate_limit import RedisRateLimitMiddleware
        app.add_middleware(
            RedisRateLimitMiddleware,
            redis_url=settings.REDIS_URL,
            requests=settings.RATE_LIMIT_PER_MINUTE,
            window_seconds=60,
        )
        print(f"Redis rate limiting enabled: {settings.RATE_LIMIT_PER_MINUTE} req/min")
    except Exception as e:
        print(f"Redis rate limiting unavailable: {e}")
else:
    print("WARNING: Redis not configured - rate limiting uses in-memory storage (not for production!)")

# Trusted Host Middleware
if not settings.DEBUG and settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # DEV-ONLY: Auto-create tables in development with SQLite
    # PRODUCTION: Use Alembic migrations via start.py (never auto-DDL)
    if settings.DEBUG and "sqlite" in settings.DATABASE_URL:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis cache (only if configured)
    from app.core.redis_cache import cache
    if settings.REDIS_URL:
        await cache.connect()
    else:
        print("Redis not configured — caching disabled")

    print(f"{settings.APP_NAME} v{settings.APP_VERSION} started")
    print(f"Environment: {settings.ENVIRONMENT}")
    if settings.DEBUG:
        print(f"API Docs: http://localhost:3000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Disconnect Redis cache
    from app.core.redis_cache import cache
    await cache.disconnect()
    
    print(f"{settings.APP_NAME} shutting down")


@app.get("/metrics", tags=["Monitoring"])
async def metrics(request: Request):
    """Prometheus metrics endpoint - PROTECTED"""
    if not settings.DEBUG:
        # SECURITY: Only accept auth via header (NOT query params - they leak in logs/referrers)
        secret_token = request.headers.get("X-Monitoring-Token")
        expected_token = settings.MONITORING_TOKEN
        if not expected_token or (secret_token is None) or secret_token != expected_token:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Monitoring endpoint requires authentication.",
            )

    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def root_health():
    """
    Lightweight root health endpoint for load balancers.
    Detailed checks remain available at /api/v1/health/.
    """
    return {"status": "healthy"}


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
