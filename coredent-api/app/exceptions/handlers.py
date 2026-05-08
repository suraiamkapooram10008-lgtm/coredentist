"""
Exception Handlers
Custom exception handlers for FastAPI
"""

import re
import traceback
import logging
import json
from decimal import Decimal
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config_simple import settings

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

PHI_KEYS = {
    "first_name", "last_name", "email", "phone", "dob", "address",
    "ssn", "insurance_id", "license", "account_number", "card_number"
}


def _redact_phi(data):
    """Recursively scrub common PHI patterns from a dictionary or list."""
    if isinstance(data, dict):
        return {
            k: "[REDACTED]" if k.lower() in PHI_KEYS else _redact_phi(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [_redact_phi(item) for item in data]
    return data


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors - hide details in production"""
    errors = exc.errors()
    
    # Convert Decimal values to float in error details
    def convert_decimals(obj):
        if isinstance(obj, dict):
            return {k: convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_decimals(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        return obj
    
    errors = convert_decimals(errors)
    
    if settings.DEBUG:
        # Safely serialize body, converting Decimals and skipping non-serializable types
        body = exc.body
        if body is not None:
            try:
                body = convert_decimals(body)
                # Verify it can be JSON serialized
                json.dumps(body)
            except (TypeError, ValueError):
                body = str(body)
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": errors,
                "body": body,
            },
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "type": "validation_error",
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors - never expose details in production + scrub PHI from logs."""
    client_host = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    url = str(request.url)

    for key in PHI_KEYS:
        url = re.sub(rf"({key}=)[^&]*", r"\1[REDACTED]", url, flags=re.IGNORECASE)

    body_display = "[NOT_JSON_OR_NOT_LOADED]"
    try:
        body = await request.json()
        body_display = str(_redact_phi(body))
    except Exception:
        pass

    logger.error(
        f"Unhandled exception: {method} {url} from {client_host}\n"
        f"Body: {body_display}\n"
        f"Error: {str(exc)}\n"
        f"Traceback: {traceback.format_exc()}",
        extra={
            "path": path,
            "method": method,
            "client": client_host,
        }
    )

    if settings.DEBUG:
        raise exc

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal error occurred. Please contact support if the problem persists.",
            "type": "server_error",
        },
    )
