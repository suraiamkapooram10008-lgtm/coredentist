"""
Communications Task Queue Handler
Bridges between Celery tasks and the unified task queue abstraction
"""

import logging
from typing import Dict, Any

from app.core.task_queue import get_task_queue
from app.core.email import EmailService, EmailProvider
from app.core.sms import SMSService, SMSProvider
from app.core.config_simple import settings
from app.models.communication import (
    PatientMessage, MessageStatus, MessageType
)

logger = logging.getLogger(__name__)


def _do_send_message(message_id: str) -> Dict[str, Any]:
    """
    Actual implementation of message sending (sync version)
    This is called by the Celery task OR by the memory queue fallback
    """
    from app.core.database import SessionLocal

    db = SessionLocal()

    try:
        message = db.query(PatientMessage).filter(PatientMessage.id == message_id).first()

        if not message:
            logger.error(f"Message not found: {message_id}")
            return {"status": "error", "error": "Message not found"}

        if message.status not in [MessageStatus.PENDING, MessageStatus.QUEUED]:
            logger.warning(f"Message {message_id} already processed, status: {message.status}")
            return {"status": "skipped", "reason": f"Message already has status {message.status}"}

        from app.models.practice import Practice
        practice = db.query(Practice).filter(Practice.id == message.practice_id).first()

        message.status = MessageStatus.SENDING
        message.sent_at = message.sent_at or datetime.now(timezone.utc)
        db.commit()

        success = False
        error_message = None
        external_id = None

        if message.message_type == MessageType.SMS:
            sms_service = SMSService(
                provider=SMSProvider.TWILIO if settings.TWILIO_ACCOUNT_SID else SMSProvider.CONSOLE
            )

            result = sms_service.send_sms(
                to=message.recipient_phone,
                message=message.content
            )

            success = result.get("status") == "sent"
            external_id = result.get("external_id")
            error_message = result.get("error")

        elif message.message_type == MessageType.EMAIL:
            email_service = EmailService(
                provider=EmailProvider.SENDGRID if settings.SENDGRID_API_KEY else EmailProvider.CONSOLE
            )

            result = email_service.send_email(
                to=message.recipient_email,
                subject=message.subject or f"Message from {practice.name if practice else 'CoreDent'}",
                html_content=message.content,
                text_content=message.content
            )

            success = result.get("status") == "sent"
            external_id = result.get("message_id")
            error_message = result.get("error")

        if success:
            message.status = MessageStatus.SENT
            message.external_id = external_id
            message.delivered_at = datetime.now(timezone.utc)
            logger.info(f"Message {message_id} sent successfully via {message.message_type}")
        else:
            message.status = MessageStatus.FAILED
            message.error_message = error_message
            logger.error(f"Message {message_id} failed: {error_message}")

        db.commit()
        return {
            "status": "sent" if success else "failed",
            "message_id": message_id,
            "external_id": external_id,
            "error": error_message
        }

    except Exception as e:
        logger.error(f"Error sending message {message_id}: {e}")
        db.rollback()

        try:
            message = db.query(PatientMessage).filter(PatientMessage.id == message_id).first()
            if message:
                message.status = MessageStatus.FAILED
                message.error_message = str(e)
                db.commit()
        except Exception:
            pass

        return {"status": "error", "error": str(e)}

    finally:
        db.close()


from datetime import datetime, timezone


def send_message_task(message_id: str) -> Dict[str, Any]:
    """
    Task to send a message - dispatches to Celery or memory queue

    This function can be called directly (sync) or via .delay() (async)
    """
    task_queue = get_task_queue()

    if task_queue.is_celery:
        from celery import shared_task
        @shared_task(bind=True, max_retries=3, default_retry_delay=60)
        def celery_task(self, msg_id):
            return _do_send_message(msg_id)
        return celery_task.delay(message_id)
    else:
        return _do_send_message(message_id)


def send_message_sync(message_id: str) -> Dict[str, Any]:
    """
    Synchronous version of send_message_task
    Use this when you need to wait for the result
    """
    return _do_send_message(message_id)
