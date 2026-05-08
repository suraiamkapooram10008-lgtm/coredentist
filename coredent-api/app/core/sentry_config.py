"""
Sentry Configuration
Error tracking with PHI redaction for HIPAA compliance
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.core.config_simple import settings

logger = logging.getLogger(__name__)
sentry_sdk = None


SENSITIVE_KEYS = [
    'password', 'token', 'secret', 'api_key', 'authorization',
    'ssn', 'social_security', 'credit_card', 'card_number',
    'patient_name', 'email', 'phone', 'address'
]


def _redact_dict(d: dict) -> dict:
    """Recursively redact sensitive keys"""
    if not isinstance(d, dict):
        return d

    for key in list(d.keys()):
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            d[key] = '[REDACTED]'
        elif isinstance(d[key], dict):
            d[key] = _redact_dict(d[key])
        elif isinstance(d[key], list):
            d[key] = [_redact_dict(item) if isinstance(item, dict) else item for item in d[key]]

    return d


def filter_sensitive_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """Filter sensitive data from Sentry events (HIPAA compliance)"""
    if 'request' in event:
        event['request'] = _redact_dict(event['request'])
    if 'extra' in event:
        event['extra'] = _redact_dict(event['extra'])
    return event


def init_sentry() -> None:
    """Initialize Sentry for error tracking"""
    global sentry_sdk

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except Exception:
        logger.info("Sentry SDK not installed")
        return

    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured - monitoring disabled")
        return

    try:
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                sentry_logging,
            ],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            environment=settings.ENVIRONMENT,
            release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
            before_send=lambda event, hint: filter_sensitive_data(event),
            attach_stacktrace=True,
            send_default_pii=False,
        )

        logger.info("Sentry monitoring initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")
        sentry_sdk = None


def log_security_event(
    event_type: str,
    severity: str,
    message: str,
    extra: Dict[str, Any] = None
) -> None:
    """Log security events to Sentry and application logs"""
    log_data = {
        'event_type': event_type,
        'severity': severity,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        **(extra or {})
    }

    if severity == 'critical':
        logger.critical(message, extra=log_data)
    elif severity == 'error':
        logger.error(message, extra=log_data)
    elif severity == 'warning':
        logger.warning(message, extra=log_data)
    else:
        logger.info(message, extra=log_data)

    if sentry_sdk:
        with sentry_sdk.push_scope() as scope:
            scope.set_tag('event_type', event_type)
            scope.set_tag('severity', severity)
            scope.set_context('security_event', log_data)

            if severity in ['error', 'critical']:
                sentry_sdk.capture_message(message, level=severity)
            else:
                sentry_sdk.add_breadcrumb(
                    category='security',
                    message=message,
                    level=severity,
                    data=log_data
                )
