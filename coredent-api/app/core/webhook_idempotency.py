"""
Webhook Idempotency Handler
Ensures webhooks are processed exactly once
"""

import hashlib
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.webhook_event import WebhookEvent

logger = logging.getLogger(__name__)


def compute_payload_hash(payload: bytes) -> str:
    """Compute SHA-256 hash of webhook payload"""
    return hashlib.sha256(payload).hexdigest()


async def is_webhook_processed(
    db: Session,
    provider: str,
    event_id: str
) -> bool:
    """
    Check if webhook event has already been processed.
    
    Args:
        db: Database session
        provider: Webhook provider (stripe, razorpay, etc.)
        event_id: Unique event ID from provider
        
    Returns:
        True if already processed, False otherwise
    """
    event = db.query(WebhookEvent).filter(
        WebhookEvent.provider == provider,
        WebhookEvent.event_id == event_id
    ).first()
    
    return event is not None and event.processed


async def mark_webhook_processing(
    db: Session,
    provider: str,
    event_id: str,
    event_type: str,
    payload: bytes
) -> WebhookEvent:
    """
    Mark webhook as being processed (idempotency lock).
    
    Args:
        db: Database session
        provider: Webhook provider
        event_id: Unique event ID
        event_type: Type of event
        payload: Raw webhook payload
        
    Returns:
        WebhookEvent record
        
    Raises:
        IntegrityError: If event already exists (duplicate)
    """
    payload_hash = compute_payload_hash(payload)
    
    webhook_event = WebhookEvent(
        provider=provider,
        event_id=event_id,
        event_type=event_type,
        payload_hash=payload_hash,
        processed=False
    )
    
    try:
        db.add(webhook_event)
        db.commit()
        db.refresh(webhook_event)
        return webhook_event
    except IntegrityError:
        db.rollback()
        # Event already exists - this is a duplicate
        logger.warning(f"Duplicate webhook event: {provider}:{event_id}")
        raise


async def mark_webhook_processed(
    db: Session,
    webhook_event: WebhookEvent,
    success: bool = True,
    error_message: str = None
):
    """
    Mark webhook as successfully processed or failed.
    
    Args:
        db: Database session
        webhook_event: WebhookEvent record
        success: Whether processing succeeded
        error_message: Error message if failed
    """
    webhook_event.processed = success
    webhook_event.processed_at = datetime.now(timezone.utc)
    
    if not success:
        webhook_event.error_message = error_message
        webhook_event.retry_count += 1
    
    db.commit()
    
    logger.info(
        f"Webhook {webhook_event.provider}:{webhook_event.event_id} "
        f"marked as {'processed' if success else 'failed'}"
    )


async def cleanup_old_webhook_events(
    db: Session,
    days_to_keep: int = 90
):
    """
    Clean up old webhook events (retention policy).
    
    Args:
        db: Database session
        days_to_keep: Number of days to retain events
    """
    from datetime import timedelta
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    
    deleted_count = db.query(WebhookEvent).filter(
        WebhookEvent.created_at < cutoff_date,
        WebhookEvent.processed == True
    ).delete()
    
    db.commit()
    
    logger.info(f"Cleaned up {deleted_count} old webhook events")
    return deleted_count
