"""
Rate Limiter - SlowAPI Integration
Provides the `limiter` instance used by endpoint decorators for fine-grained rate limiting.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global limiter instance used by rate-limited endpoints
# Uses IP-based rate limiting by default
limiter = Limiter(key_func=get_remote_address)