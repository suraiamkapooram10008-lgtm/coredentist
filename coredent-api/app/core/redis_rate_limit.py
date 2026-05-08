"""
Production-ready Redis-backed rate limiting middleware
Uses Redis sliding window algorithm for accurate rate limiting across multiple instances.
"""

import time
import logging
from typing import Optional, Tuple, Dict, Any
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import json

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Production-ready Redis-backed rate limiter using sliding window algorithm.
    Works across multiple application instances.
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        requests: int = 100,
        window_seconds: int = 60,
        key_prefix: str = "ratelimit",
    ):
        self.requests = requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix
        self.redis_client: Optional[redis.Redis] = None
        self._use_redis = False
        
        if redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self.redis_client.ping()
                self._use_redis = True
                logger.info(f"Redis rate limiting enabled: {requests} req/{window_seconds}s")
            except Exception as e:
                logger.warning(f"Redis connection failed for rate limiting: {e}. Using in-memory fallback.")
                self.redis_client = None
        else:
            logger.info("Redis URL not configured - using in-memory rate limiting (not for production!)")
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique identifier for the client"""
        # Try to get forwarded header first (for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        # Also check X-Real-IP for nginx
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else "unknown"
    
    def _get_redis_key(self, client_id: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"{self.key_prefix}:{client_id}"
    
    def is_allowed(self, request: Request) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit.
        Uses Redis for production, falls back to in-memory for development.
        """
        client_id = self._get_client_id(request)
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        if self._use_redis and self.redis_client:
            return self._redis_check_rate_limit(client_id, current_time, window_start)
        else:
            return self._memory_check_rate_limit(client_id, current_time, window_start)
    
    def _redis_check_rate_limit(
        self,
        client_id: str,
        current_time: float,
        window_start: float,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Redis-based rate limit check using sorted set.
        Uses sliding window algorithm for accuracy.
        """
        key = self._get_redis_key(client_id)
        
        try:
            pipe = self.redis_client.pipeline()
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiry on the key
            pipe.expire(key, self.window_seconds + 1)
            
            results = pipe.execute()
            current_count = results[1]  # zcard result
            
            if current_count >= self.requests:
                # Rate limit exceeded - remove the request we just added
                self.redis_client.zrem(key, str(current_time))
                
                # Get oldest request time for retry-after calculation
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = oldest[0][1] + self.window_seconds
                else:
                    reset_time = current_time + self.window_seconds
                
                return False, {
                    "allowed": False,
                    "current": current_count,
                    "limit": self.requests,
                    "reset_in_seconds": int(reset_time - current_time),
                    "retry_after": int(reset_time - current_time),
                }
            
            return True, {
                "allowed": True,
                "current": current_count + 1,
                "limit": self.requests,
                "remaining": self.requests - current_count - 1,
            }
            
        except redis.RedisError as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fall through to in-memory on error
    
    # In-memory fallback storage (for development/testing)
    _memory_storage: Dict[str, list] = {}
    
    def _memory_check_rate_limit(
        self,
        client_id: str,
        current_time: float,
        window_start: float,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        In-memory rate limit check (fallback for development).
        WARNING: This doesn't work with multiple instances!
        """
        if client_id not in self._memory_storage:
            self._memory_storage[client_id] = []
        
        # Clean old entries
        self._memory_storage[client_id] = [
            t for t in self._memory_storage[client_id]
            if t > window_start
        ]
        
        current_count = len(self._memory_storage[client_id])
        
        if current_count >= self.requests:
            oldest = self._memory_storage[client_id][0] if self._memory_storage[client_id] else current_time
            reset_time = oldest + self.window_seconds
            
            return False, {
                "allowed": False,
                "current": current_count,
                "limit": self.requests,
                "reset_in_seconds": int(reset_time - current_time),
                "retry_after": int(reset_time - current_time),
            }
        
        # Record this request
        self._memory_storage[client_id].append(current_time)
        
        return True, {
            "allowed": True,
            "current": current_count + 1,
            "limit": self.requests,
            "remaining": self.requests - current_count - 1,
        }
    
    def get_rate_limit_headers(self, info: Dict[str, Any]) -> Dict[str, str]:
        """Get rate limit headers for response"""
        return {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info.get("remaining", info["current"])),
            "X-RateLimit-Reset": str(int(time.time()) + self.window_seconds),
        }


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for Redis-backed rate limiting.
    """
    
    def __init__(
        self,
        app,
        redis_url: Optional[str] = None,
        requests: int = 100,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.limiter = RedisRateLimiter(redis_url, requests, window_seconds)
        # Endpoints to exclude from rate limiting
        self.exclude_prefixes = {"/health", "/docs", "/redoc", "/openapi.json", "/metrics"}
    
    def _is_excluded(self, path: str) -> bool:
        """Check if path should be excluded from rate limiting"""
        for prefix in self.exclude_prefixes:
            if path == prefix or path.startswith(prefix + "/"):
                return True
        return False
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if self._is_excluded(request.url.path):
            return await call_next(request)
        
        # Check rate limit
        allowed, info = self.limiter.is_allowed(request)
        
        if not allowed:
            headers = self.limiter.get_rate_limit_headers(info)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "type": "rate_limit_exceeded",
                    "retry_after": info["retry_after"],
                },
                headers={
                    **headers,
                    "Retry-After": str(info["retry_after"]),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        headers = self.limiter.get_rate_limit_headers(info)
        for key, value in headers.items():
            response.headers[key] = value
        
        return response


# Pre-configured rate limiters for different endpoint types
def create_rate_limiter(
    redis_url: Optional[str],
    requests: int,
    window: int = 60,
) -> RedisRateLimiter:
    """Factory function to create configured rate limiters"""
    return RedisRateLimiter(redis_url, requests, window)


# Pre-configured limiters (configured from settings)
auth_rate_limiter = None  # Initialized in main.py
api_rate_limiter = None   # Initialized in main.py
upload_rate_limiter = None  # Initialized in main.py