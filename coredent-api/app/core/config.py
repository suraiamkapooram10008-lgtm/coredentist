"""
Configuration re-export
Canonical settings are in app.core.config_simple
This file exists for backward compatibility.
"""

from app.core.config_simple import settings

__all__ = ["settings"]
