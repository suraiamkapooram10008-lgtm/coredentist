"""
HTTPS Enforcement Middleware
Ensures all production traffic goes through HTTPS
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from app.core.config_simple import settings


class HTTPSEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Redirects HTTP requests to HTTPS in production.
    Skips for localhost/development.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip if not production
        if settings.ENVIRONMENT != "production":
            return await call_next(request)
        
        # Skip if already HTTPS or localhost
        if request.url.scheme == "https":
            return await call_next(request)
        
        if request.url.hostname in ["localhost", "127.0.0.1", "test", "::1"]:
            return await call_next(request)
        
        # Redirect to HTTPS
        https_url = request.url.replace(scheme="https")
        
        # Handle default ports
        if request.url.port == 80:
            https_url = https_url.replace(port=443)
        
        # Use 302 (temporary) instead of 301 (permanent) to allow testing flexibility
        return RedirectResponse(url=str(https_url), status_code=302)
