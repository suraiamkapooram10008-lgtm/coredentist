"""
Audit Logging Middleware
HIPAA-compliant API request logging
"""

import time
import logging
from datetime import datetime, timezone
from fastapi import Request
from app.core.config_simple import settings
from app.core.security import decode_token

logger = logging.getLogger(__name__)


async def audit_logging_middleware(request: Request, call_next):
    """Log all API requests for HIPAA audit trail"""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)

    # Only log API requests (not health checks, metrics, docs)
    if request.url.path.startswith("/api/"):
        user_id = None
        practice_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                token = auth_header[7:]
                payload = decode_token(token)
                if payload:
                    user_id = payload.get("sub")
                    practice_id = payload.get("practice_id")
            except Exception:
                pass

        # CRIT-11 FIX: Redact PHI from query parameters before logging
        query_params = dict(request.query_params)
        phi_keys = {"query", "q", "email", "phone", "name", "first_name", "last_name", "address"}
        redacted_query = {
            k: "[REDACTED]" if k.lower() in phi_keys else v
            for k, v in query_params.items()
        }

        # CRIT-10 FIX: Use centralized IP resolution
        from app.core.request_utils import get_client_ip
        client_ip = get_client_ip(request)

        logger.info(
            "API_REQUEST",
            extra={
                "audit": True,
                "method": request.method,
                "path": request.url.path,
                "query": redacted_query if redacted_query else None,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
                "practice_id": practice_id,
                "ip_address": client_ip,
                "user_agent": request.headers.get("user-agent"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    return response
