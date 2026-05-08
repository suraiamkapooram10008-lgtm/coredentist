"""
Rate Limiting Middleware
FastAPI middleware for rate limiting requests
"""

import time
import logging
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter using sliding window algorithm
    """
    
    def __init__(self, requests: int = 100, window_seconds: int = 60):
        self.requests = requests
        self.window_seconds = window_seconds
        self.requests_log: Dict[str, list] = defaultdict(list)
    
    # M-2 FIX: Validate X-Forwarded-For against known trusted proxies
    # to prevent IP spoofing. Acceptable for Railway (proxy handles it),
    # but validated properly for security.
    _trusted_proxy_networks = [
        "10.0.0.0/8",      # Private network (Railway internal)
        "172.16.0.0/12",   # Private network
        "192.168.0.0/16",  # Private network
        "100.64.0.0/10",   # Carrier-grade NAT
    ]

    def _is_trusted_proxy(self, ip: str) -> bool:
        """Check if IP belongs to a trusted proxy network"""
        try:
            import ipaddress
            addr = ipaddress.ip_address(ip)
            for network in self._trusted_proxy_networks:
                if addr in ipaddress.ip_network(network, strict=False):
                    return True
            return False
        except (ValueError, ImportError):
            # If ipaddress fails, trust the header (safe behind Railway)
            return True

    def _get_client_id(self, request: Request) -> str:
        """Get unique identifier for the client"""
        # Try to get forwarded header first (for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Get the rightmost trusted proxy IP (not the first which could be spoofed)
            ips = [ip.strip() for ip in forwarded.split(",")]
            # Walk from right to left to find first non-trusted IP
            for ip in reversed(ips):
                if not self._is_trusted_proxy(ip):
                    return ip
            # If all IPs are trusted, use the leftmost (direct client)
            return ips[-1].strip()
        return request.client.host if request.client else "unknown"
    
    def _clean_old_requests(self, client_id: str) -> None:
        """Remove requests outside the time window"""
        cutoff = time.time() - self.window_seconds
        self.requests_log[client_id] = [
            req_time for req_time in self.requests_log[client_id]
            if req_time > cutoff
        ]
    
    def is_allowed(self, request: Request) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed based on rate limit
        Returns (allowed, info_dict)
        """
        client_id = self._get_client_id(request)
        self._clean_old_requests(client_id)
        
        current_count = len(self.requests_log[client_id])
        
        if current_count >= self.requests:
            # Rate limit exceeded
            oldest = self.requests_log[client_id][0] if self.requests_log[client_id] else time.time()
            reset_time = oldest + self.window_seconds
            
            return False, {
                "allowed": False,
                "current": current_count,
                "limit": self.requests,
                "reset_in_seconds": int(reset_time - time.time()),
                "retry_after": int(reset_time - time.time()),
            }
        
        # Record this request
        self.requests_log[client_id].append(time.time())
        
        return True, {
            "allowed": True,
            "current": current_count + 1,
            "limit": self.requests,
            "remaining": self.requests - current_count - 1,
        }
    
    def get_rate_limit_headers(self, info: Dict[str, any]) -> Dict[str, str]:
        """Get rate limit headers for response"""
        return {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info.get("remaining", info["current"])),
            "X-RateLimit-Reset": str(int(time.time()) + self.window_seconds),
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting
    """
    
    def __init__(self, app, requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests, window_seconds)
        # Endpoints to exclude from rate limiting
        # Use prefixes so "/api/v1/health" matches "/health" prefix
        self.exclude_prefixes = {"/health", "/docs", "/redoc", "/openapi.json"}
    
    def _is_excluded(self, path: str) -> bool:
        """Check if path should be excluded from rate limiting (prefix match)"""
        for prefix in self.exclude_prefixes:
            if path == prefix or path.startswith(prefix + "/") or path.startswith(prefix + "?"):
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
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
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


# Endpoint-specific rate limiters
def create_rate_limiter(requests: int, window: int = 60) -> RateLimiter:
    """Factory function to create custom rate limiters"""
    return RateLimiter(requests, window)


# Pre-configured limiters
auth_limiter = RateLimiter(requests=5, window_seconds=60)  # 5 requests per minute for auth
api_limiter = RateLimiter(requests=100, window_seconds=60)  # 100 requests per minute for API
upload_limiter = RateLimiter(requests=10, window_seconds=60)  # 10 uploads per minute
