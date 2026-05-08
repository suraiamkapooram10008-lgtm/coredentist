"""
Security Monitoring Middleware
Track and log security-relevant events
"""

import time
from fastapi import Request
from app.core.sentry_config import log_security_event


async def security_monitoring_middleware(request: Request, call_next):
    """
    Monitor and log security-relevant events

    Tracks:
    - Failed authentication attempts
    - Rate limit violations
    - Suspicious request patterns
    - Error rates
    """
    start_time = time.time()

    try:
        response = await call_next(request)

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
