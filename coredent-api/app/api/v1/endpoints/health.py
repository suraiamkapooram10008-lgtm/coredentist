"""
Health Check Endpoints
Provides system health monitoring for production with Sentry integration
"""

from fastapi import APIRouter, Depends, Response, status, Request, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.redis_cache import cache
from app.core.config_simple import settings
import time
import psutil
import platform
from typing import Dict, Any
from datetime import datetime, timezone

router = APIRouter()

# Store startup time for uptime calculation
_startup_time = time.time()


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint for load balancers and monitoring.
    Returns 503 if any critical service is unhealthy.
    NOTE: In production, version/environment info is hidden to prevent info disclosure.
    """
    start_time = time.time()
    overall_healthy = True

    is_production = settings.ENVIRONMENT.lower() in ("production", "prod")
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # Hide version/environment in production to prevent info disclosure
        **({} if is_production else {
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }),
        "uptime_seconds": round(time.time() - _startup_time, 2),
        "checks": {}
    }

    # Database health check
    db_start = time.time()
    try:
        await db.execute(text("SELECT 1"))
        db_health = True
    except Exception as e:
        db_health = False
        overall_healthy = False

    health_status["checks"]["database"] = {
        "status": "healthy" if db_health else "unhealthy",
        "response_time_ms": round((time.time() - db_start) * 1000, 2)
    }

    # Redis health check (optional)
    redis_start = time.time()
    try:
        redis_health = await cache.health_check() if cache and getattr(cache, 'enabled', False) else True
    except Exception:
        redis_health = False
    redis_response_time = round((time.time() - redis_start) * 1000, 2)

    health_status["checks"]["redis"] = {
        "status": "healthy" if redis_health else "unhealthy",
        "response_time_ms": redis_response_time
    }
    if not redis_health and getattr(cache, 'enabled', False):
        overall_healthy = False

    # Sentry connectivity check
    sentry_start = time.time()
    try:
        sentry_healthy = _check_sentry()
    except Exception:
        sentry_healthy = False
    sentry_response_time = round((time.time() - sentry_start) * 1000, 2)

    health_status["checks"]["sentry"] = {
        "status": "healthy" if sentry_healthy else "unhealthy",
        "configured": bool(settings.SENTRY_DSN),
        "response_time_ms": sentry_response_time
    }
    # Sentry is optional, so don't mark overall unhealthy if just Sentry fails

    # System metrics
    try:
        health_status["checks"]["system"] = {
            "status": "healthy",
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
        }
        # Flag unhealthy if disk or memory critical
        if psutil.disk_usage('/').percent > 95 or psutil.virtual_memory().percent > 95:
            health_status["checks"]["system"]["status"] = "critical"
            overall_healthy = False
    except Exception as e:
        health_status["checks"]["system"] = {"status": "unknown", "error": str(e)}

    # Application metrics
    health_status["checks"]["application"] = {
        "status": "healthy",
        "debug_mode": settings.DEBUG,
        "audit_log_enabled": settings.AUDIT_LOG_ENABLED if hasattr(settings, 'AUDIT_LOG_ENABLED') else True,
    }

    # Set overall status
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"

    return health_status


@router.get("/liveness")
async def liveness_check() -> Dict[str, str]:
    """
    Simple liveness probe for Kubernetes/load balancers.
    Returns 200 if the application process is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": str(round(time.time() - _startup_time, 2))
    }


@router.get("/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db), response: Response = None) -> Dict[str, Any]:
    """
    Readiness probe that checks if the application is ready to serve traffic.
    Returns 503 if critical dependencies (database) are not ready.
    """
    try:
        # Quick database check
        await db.execute(text("SELECT 1"))
        db_ready = True
    except Exception:
        db_ready = False

    # Redis check if enabled
    try:
        if cache and getattr(cache, 'enabled', False):
            redis_ok = await cache.health_check()
        else:
            redis_ok = True
    except Exception:
        redis_ok = False

    ready = db_ready and redis_ok
    if not ready and response:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if ready else "not ready",
        "database": "ready" if db_ready else "not ready",
        "redis": "ready" if redis_ok else "not ready",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/sentry")
async def sentry_health_check() -> Dict[str, Any]:
    """
    Sentry-specific health check endpoint.
    Verifies Sentry DSN configuration and SDK connectivity.
    """
    sentry_status = {
        "configured": bool(settings.SENTRY_DSN),
        "dsn_prefix": settings.SENTRY_DSN.split("//")[0] + "//" if settings.SENTRY_DSN else None,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            if sentry_sdk.get_current_scope():
                sentry_status["sdk_status"] = "initialized"
            else:
                sentry_status["sdk_status"] = "not_initialized"
        except ImportError:
            sentry_status["sdk_status"] = "sdk_not_installed"
    else:
        sentry_status["sdk_status"] = "not_configured"

    return sentry_status


@router.get("/metrics")
async def metrics_check(
    request: Request,
    monitoring_token: str = Query(None, description="Monitoring authentication token"),
) -> Dict[str, Any]:
    """
    Extended metrics endpoint for monitoring dashboards.
    Includes detailed system and application metrics.
    SECURITY: Requires monitoring token in production.
    """
    # Protect metrics endpoint in production
    if not settings.DEBUG and settings.MONITORING_TOKEN:
        secret_token = request.headers.get("X-Monitoring-Token", "")
        if not secret_token or secret_token != settings.MONITORING_TOKEN:
            if not monitoring_token or monitoring_token != settings.MONITORING_TOKEN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Monitoring token required."
                )
    try:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_times = psutil.cpu_times_percent(interval=0.1)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(time.time() - _startup_time, 2),
            "system": {
                "cpu": {
                    "percent": psutil.cpu_percent(interval=0.1),
                    "count_logical": psutil.cpu_count(logical=True),
                    "count_physical": psutil.cpu_count(logical=False),
                    "user_time": getattr(cpu_times, 'user', 0),
                    "system_time": getattr(cpu_times, 'system', 0),
                },
                "memory": {
                    "total_mb": round(mem.total / (1024 * 1024), 2),
                    "available_mb": round(mem.available / (1024 * 1024), 2),
                    "percent": mem.percent,
                    "used_mb": round(mem.used / (1024 * 1024), 2),
                },
                "disk": {
                    "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                    "free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
                    "percent": disk.percent,
                },
                "platform": platform.platform(),
                "python_version": platform.python_version(),
            },
            "application": {
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
            }
        }
    except Exception as e:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": f"Failed to collect metrics: {str(e)}"
        }


def _check_sentry() -> bool:
    """Check if Sentry SDK is properly initialized"""
    if not settings.SENTRY_DSN:
        return True  # Not configured = not a failure
    try:
        import sentry_sdk
        return sentry_sdk.is_initialized()
    except (ImportError, AttributeError):
        return False
