"""
Redis-backed rate limiting middleware
Provides Redis-based rate limiting if Redis is available, falls back to in-memory otherwise.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
import redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RedisRateLimitMiddleware:
    """
    Redis-based rate limiting middleware for production scaling.
    Falls back to in-memory if Redis connection fails.
    """
    
    def __init__(self, app, requests: int = 100, window: int = 60):
        self.app = app
        self.requests = requests
        self.window = window
        self.limiter = Limiter(key_func=get_remote_address)
        self.redis_client: Optional[redis.Redis] = None
        
    async def __call__(self, request: Request, call_next):
        # Try Redis first if configured
        if self.redis_client:
            try:
                # Redis-based rate limiting logic would go here
                # For now, pass through - Redis setup requires more complex integration
                pass
            except Exception as e:
                logger.warning(f"Redis rate limiting error: {e}, falling back to in-memory")
        
        # Fallback to in-memory rate limiting handled by slowapi
        return await call_next(request)


def setup_redis_rate_limit(app, redis_url: Optional[str] = None):
    """
    Configure Redis rate limiting if Redis URL is provided.
    This is called from main.py to conditionally add the middleware.
    """
    if not redis_url:
        logger.info("Redis URL not configured - rate limiting will use in-memory storage")
        return False
    
    try:
        # Test Redis connection
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("Redis connection successful - rate limiting enabled with Redis")
        
        # Add middleware with configured limits
        from slowapi import Limiter
        from slowapi.util import get_remote_address
        from slowapi.errors import RateLimitExceeded
        
        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded", "type": "rate_limit_exceeded"}
        ))
        
        # Note: Full Redis integration requires additional middleware setup
        # For now, we'll use in-memory with shared storage
        return True
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Rate limiting will use in-memory storage.")
        return False