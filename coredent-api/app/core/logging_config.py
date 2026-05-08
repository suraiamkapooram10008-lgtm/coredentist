"""
Logging Configuration
Production JSON logging for HIPAA compliance
"""

import logging
from datetime import datetime, timezone
from pythonjsonlogger import jsonlogger
from app.core.config_simple import settings


def setup_logging() -> None:
    """Configure structured JSON logging for production"""
    if settings.ENVIRONMENT != "production":
        return

    class CustomJsonFormatter(jsonlogger.JsonFormatter):
        def add_fields(self, record, message, extra):
            super().add_fields(record, message, extra)
            record['timestamp'] = datetime.now(timezone.utc).isoformat()
            record['level'] = record.levelname
            record['service'] = settings.APP_NAME

    handler = logging.StreamHandler()
    handler.setFormatter(CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s'))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
