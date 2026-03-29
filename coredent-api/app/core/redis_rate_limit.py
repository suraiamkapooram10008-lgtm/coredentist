"""
Redis-backed Rate Limiting Middleware
For distributed/horizontal scaling environments
"""

import time
import logging
from typing import Optional
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis_client():
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        from app.core.config import settings
        if settings.REDIS_URL:
            try:
                import redis
                _redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                )
                _redis_client.ping()
                logger.info("Redis rate limiter initialized")
            except Exception as e:
                logger.warning(f"Redis unavailable for rate limiting: {e}")
                return None
        return None
    return _redis_client


class RedisRateLimiter:
    """
    Redis-backed rate limiter using sliding window
    Supports distributed rate limiting across multiple instances
    """
    
    def __init__(self, requests: int = 100, window_seconds: int = 60):
        self.requests = requests
        self.window_seconds = window_seconds
        self.redis = get_redis_client()
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique identifier for the client"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"rl:{forwarded.split(',')[0].strip()}"
        
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        if forwarded_proto:
            return f"rl:{request.client.host}:{forwarded_proto}"
        
        return f"rl:{request.client.host if request.client else 'unknown'}"
    
    def is_allowed(self, request: Request) -> tuple[bool, dict]:
        """Check if request is allowed using Redis"""
        if not self.redis:
            return True, {"allowed": True, "source": "memory"}
        
        key = self._get_client_id(request)
        now = time.time()
        window_start = now - self.window_seconds
        
        try:
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.window_seconds)
            results = pipe.execute()
            
            current_count = results[1]
            
            if current_count >= self.requests:
                ttl = self.redis.ttl(key)
                return False, {
                    "allowed": False,
                    "current": current_count,
                    "limit": self.requests,
                    "retry_after": ttl if ttl > 0 else self.window_seconds,
                    "source": "redis",
                }
            
            return True, {
                "allowed": True,
                "current": current_count + 1,
                "limit": self.requests,
                "remaining": self.requests - current_count - 1,
                "source": "redis",
            }
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            return True, {"allowed": True, "source": "fallback"}


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for Redis-backed rate limiting"""
    
    def __init__(self, app, requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = RedisRateLimiter(requests, window_seconds)
        self.exclude_paths = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        allowed, info = self.limiter.is_allowed(request)
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": info.get("retry_after", 60),
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(info.get("retry_after", 60)),
                }
            )
        
        response = await call_next(request)
        
        if info.get("source") == "redis":
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        
        return response


redis_auth_limiter = RedisRateLimiter(requests=5, window_seconds=60)
redis_api_limiter = RedisRateLimiter(requests=100, window_seconds=60)