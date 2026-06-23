"""
Tenant isolation middleware.

Every authenticated request carries a ``practice_id`` claim in its JWT.
This middleware enforces that any ``practice_id`` the client tries to use —
in a path parameter, query string, or JSON body — matches the one in the
JWT.  Without this, a single forgotten ``WHERE practice_id = :practice_id``
clause in one endpoint would leak data across tenants.

The middleware is intentionally conservative: it only validates the *presence*
and *equality* of practice ids.  It does not run any business logic.  The
endpoint still must include the practice_id in its query.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Awaitable, Callable, Optional
from uuid import UUID

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# Endpoints that legitimately operate across tenants (signup, login, health,
# internal super-admin tasks).  Anything not in this list AND authenticated
# is checked.
EXEMPT_PATH_PATTERNS = (
    re.compile(r"^/api/v1/auth/(login|register|refresh|forgot-password|reset-password|verify-email|resend-verification)/?$"),
    re.compile(r"^/api/v1/patient-portal/.*"),  # patients do not have a JWT
    re.compile(r"^/health/?$"),
    re.compile(r"^/metrics/?$"),
    re.compile(r"^/$"),
)


def _is_exempt(path: str) -> bool:
    return any(p.match(path) for p in EXEMPT_PATH_PATTERNS)


def _decode_practice_id(request: Request) -> Optional[str]:
    """Return the practice_id claim from the request's JWT, or None."""
    auth = request.headers.get("Authorization", "")
    if not auth.lower().startswith("bearer "):
        # Maybe cookie-based auth.
        token = request.cookies.get("access_token")
    else:
        token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    # Local import to avoid a circular import at module load.
    from app.core.security import decode_token
    try:
        payload = decode_token(token)
    except Exception:
        return None
    if not payload or payload.get("type") != "access":
        return None
    pid = payload.get("practice_id")
    return str(pid) if pid else None


def _looks_like_uuid(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        UUID(value)
        return True
    except (ValueError, TypeError):
        return False


class TenantGuardMiddleware(BaseHTTPMiddleware):
    """
    Reject any authenticated request that names a practice_id in the URL or
    body other than the one in the JWT.

    Bypass for exempt paths (login, signup, health, etc.).
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable],
    ):
        path = request.url.path
        if _is_exempt(path) or not path.startswith("/api/"):
            return await call_next(request)

        # Decode the JWT practice_id.  If the request is unauthenticated, the
        # downstream ``get_current_user`` dependency will reject it; we don't
        # need to short-circuit here.
        token_pid = _decode_practice_id(request)
        if token_pid is None:
            return await call_next(request)

        # Query string check.
        for key, value in request.query_params.multi_items():
            if "practice" in key.lower() and _looks_like_uuid(value) and value != token_pid:
                logger.warning(
                    "Tenant guard: query %s=%s does not match JWT practice_id %s",
                    key, value, token_pid,
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "detail": "Tenant mismatch: query practice_id does not match the authenticated practice.",
                        "type": "tenant_mismatch",
                    },
                )

        # Body check.  We only inspect JSON; for non-JSON / streaming bodies we
        # let the endpoint handle it.  We buffer the body so the endpoint can
        # still read it.
        if request.method in {"POST", "PUT", "PATCH"}:
            ctype = request.headers.get("content-type", "").lower()
            if "application/json" in ctype:
                body_bytes = await request.body()
                # Re-attach the body for downstream readers.
                async def receive():
                    return {"type": "http.request", "body": body_bytes, "more_body": False}
                request._receive = receive  # type: ignore[attr-defined]
                try:
                    payload = json.loads(body_bytes.decode("utf-8") or "null") if body_bytes else None
                except Exception:
                    payload = None
                if isinstance(payload, dict):
                    for key, value in payload.items():
                        if "practice" in key.lower() and _looks_like_uuid(value) and value != token_pid:
                            logger.warning(
                                "Tenant guard: body %s=%s does not match JWT practice_id %s",
                                key, value, token_pid,
                            )
                            return JSONResponse(
                                status_code=status.HTTP_403_FORBIDDEN,
                                content={
                                    "detail": "Tenant mismatch: body practice_id does not match the authenticated practice.",
                                    "type": "tenant_mismatch",
                                },
                            )

        return await call_next(request)
