"""
Token Revocation (Access-Token Blacklist)
=========================================

When a user logs out, their *refresh* token session is deleted from the DB,
preventing new access tokens from being minted.  However, the current access
token (short-lived, default 15 min) remains valid until it expires.

For defense-in-depth — particularly HIPAA session management — we maintain a
**revocation set** in Redis (with an in-process fallback for dev).  On logout,
the access token's ``jti`` (JWT ID) is added to the set with a TTL equal to
the remaining token lifetime.  On every authenticated request, ``get_current_user``
checks the set and rejects revoked tokens.

This is cheap: one Redis GET per request, TTL ensures automatic cleanup.
"""

from __future__ import annotations

import logging
from collections import deque

from app.core.config_simple import settings

logger = logging.getLogger(__name__)

# In-process fallback (dev only — NOT shared across workers).
_fallback: deque[str] = deque(maxlen=10_000)


def _redis():
    """Return a Redis client or None."""
    if not settings.REDIS_URL:
        return None
    try:
        import redis as redis_lib
        return redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None


def revoke_token(jti: str, ttl_seconds: int) -> None:
    """
    Add *jti* to the revocation set.

    *ttl_seconds* should be the remaining lifetime of the token so the key
    self-expires and Redis memory stays bounded.
    """
    if not jti or ttl_seconds <= 0:
        return
    r = _redis()
    if r:
        try:
            r.set(f"revoked:{jti}", "1", ex=ttl_seconds)
            return
        except Exception as exc:
            logger.warning("Redis revoke failed, using in-process fallback: %s", exc)
    _fallback.append(jti)


def is_revoked(jti: str) -> bool:
    """Return True if the token identified by *jti* has been revoked."""
    if not jti:
        return False
    r = _redis()
    if r:
        try:
            return r.exists(f"revoked:{jti}") == 1
        except Exception as exc:
            logger.warning("Redis is_revoked check failed, using fallback: %s", exc)
    return jti in _fallback
