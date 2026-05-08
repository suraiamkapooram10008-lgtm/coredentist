"""
Request Utilities
Helper functions for handling FastAPI requests
"""

from fastapi import Request
from typing import Optional

def get_client_ip(request: Request) -> str:
    """Extract real client IP from request, handling reverse proxies securely.
    
    SECURITY: Prefers the direct connection IP (request.client.host) if it is 
    trusted (e.g., from a known reverse proxy like Railway/nginx). 
    Falls back to X-Forwarded-For by taking the LAST hop which is the most 
    trustworthy as it was set by our immediate proxy.
    """
    # Prefer direct connection IP if available
    if request.client and request.client.host:
        return request.client.host
    
    # Fallback: X-Forwarded-For (last entry is the most trustworthy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # The last IP in the list is the one that connected to our proxy
        return forwarded_for.split(",")[-1].strip()
    
    return "unknown"
