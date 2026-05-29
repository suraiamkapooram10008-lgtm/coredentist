"""
Communications Celery Tasks
Handles async message sending for SMS/Email via task queue
"""

from celery import shared_task
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict, Any

from app.core.celery_app import celery_app
from app.core.email import EmailService, EmailProvider
from app.core.sms import SMSService, SMSProvider
from app.core.config_simple import settings
from app.models.communication import (
    PatientMessage, MessageTemplate, MessageStatus, MessageType, MessageDirection
)
from app.models.patient import Patient
from app.models.practice import Practice

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session for Celery tasks"""
    from app.core.database import SessionLocal
    return SessionLocal()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_message_task(self, message_id: str) -> Dict[str, Any]:
    """
    Celery task to send a message via SMS or Email
    
    Args:
        message_id: UUID of the PatientMessage to send
        
    Returns:
        Dict with status and details
    """
    db = get_db_session()
    
    try:
        message = db.query(PatientMessage).filter(PatientMessage.id == message_id).first()
        
        if not message:
            logger.error(f"Message not found: {message_id}")
            return {"status": "error", "error": "Message not found"}
        
        if message.status not in [MessageStatus.PENDING, MessageStatus.QUEUED]:
            logger.warning(f"Message {message_id} already processed, status: {message.status}")
            return {"status": "skipped", "reason": f"Message already has status {message.status}"}
        
        practice = db.query(Practice).filter(Practice.id == message.practice_id).first()
        patient = db.query(Patient).filter(Patient.id == message.patient_id).first()
        
        message.status = MessageStatus.SENDING
        message.sent_at = datetime.utcnow()
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
            message.delivered_at = datetime.utcnow()
            logger.info(f"Message {message_id} sent successfully via {message.message_type}")
        else:
            message.status = MessageStatus.FAILED
            message.error_message = error_message
            logger.error(f"Message {message_id} failed: {error_message}")
            
            raise self.retry(exc=Exception(error_message or "Send failed"))
        
        db.commit()
        return {
            "status": "sent",
            "message_id": message_id,
            "external_id": external_id
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
        
        raise self.retry(exc=e, countdown=120)
    
    finally:
        db.close()


@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def send_bulk_messages_task(
    self,
    message_ids: List[str],
    channel: str = "sms"
) -> Dict[str, Any]:
    """
    Celery task to send multiple messages in batch
    
    Args:
        message_ids: List of message UUIDs to send
        channel: Message channel (sms/email)
        
    Returns:
        Dict with batch send results
    """
    sent_count = 0
    failed_count = 0
    skipped_count = 0
    results = []
    
    for message_id in message_ids:
        try:
            result = send_message_task(message_id)
            if result.get("status") == "sent":
                sent_count += 1
            elif result.get("status") == "skipped":
                skipped_count += 1
            else:
                failed_count += 1
            results.append({"message_id": message_id, "result": result})
        except Exception as e:
            failed_count += 1
            results.append({"message_id": message_id, "error": str(e)})
            logger.error(f"Failed to process message {message_id} in bulk send: {e}")
    
    logger.info(
        f"Bulk send completed: {sent_count} sent, {failed_count} failed, {skipped_count} skipped"
    )
    
    return {
        "status": "completed",
        "total": len(message_ids),
        "sent": sent_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "results": results
    }


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_template_message_task(
    self,
    patient_id: str,
    template_id: str,
    channel: str,
    practice_id: str,
    context_variables: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Celery task to send a message using a template
    
    Args:
        patient_id: UUID of the patient
        template_id: UUID of the message template
        channel: Message channel (sms/email)
        practice_id: UUID of the practice
        context_variables: Dict of variables to replace in template
        
    Returns:
        Dict with send status
    """
    db = get_db_session()
    
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        practice = db.query(Practice).filter(Practice.id == practice_id).first()
        
        if not all([patient, template, practice]):
            missing = []
            if not patient: missing.append("patient")
            if not template: missing.append("template")
            if not practice: missing.append("practice")
            return {"status": "error", "error": f"Missing: {', '.join(missing)}"}
        
        context = context_variables or {}
        context.setdefault("patient_name", patient.first_name)
        context.setdefault("practice_name", practice.name)
        
        content = template.content
        for key, value in context.items():
            content = content.replace(f"[{key}]", str(value))
        
        recipient_phone = patient.phone if channel == "sms" else None
        recipient_email = patient.email if channel == "email" else None
        
        message = PatientMessage(
            practice_id=practice_id,
            patient_id=patient_id,
            template_id=template_id,
            message_type=MessageType.SMS if channel == "sms" else MessageType.EMAIL,
            direction=MessageDirection.OUTBOUND,
            status=MessageStatus.PENDING,
            subject=template.subject if template.subject else None,
            content=content,
            recipient_phone=recipient_phone,
            recipient_email=recipient_email
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        send_message_task.delay(str(message.id))
        
        template.times_used += 1
        db.commit()
        
        return {
            "status": "queued",
            "message_id": str(message.id),
            "template_id": template_id,
            "patient_id": patient_id
        }
        
    except Exception as e:
        logger.error(f"Error in send_template_message_task: {e}")
        db.rollback()
        raise self.retry(exc=e)
    
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_scheduled_messages_task(self) -> Dict[str, Any]:
    """
    Process messages that are scheduled for future delivery
    
    Finds all PENDING messages with a scheduled_at time that has passed
    and queues them for sending.
    
    Returns:
        Dict with processing results
    """
    db = get_db_session()
    
    try:
        now = datetime.utcnow()
        
        messages_to_send = db.query(PatientMessage).filter(
            PatientMessage.status == MessageStatus.PENDING,
            PatientMessage.scheduled_at <= now,
            PatientMessage.scheduled_at.isnot(None)
        ).limit(100).all()
        
        queued_count = 0
        for message in messages_to_send:
            try:
                send_message_task.delay(str(message.id))
                queued_count += 1
            except Exception as e:
                logger.error(f"Failed to queue message {message.id}: {e}")
        
        logger.info(f"Scheduled messages processed: {queued_count} queued")
        return {
            "status": "completed",
            "processed": len(messages_to_send),
            "queued": queued_count
        }
        
    except Exception as e:
        logger.error(f"Error in process_scheduled_messages_task: {e}")
        raise self.retry(exc=e)
    
    finally:
        db.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def retry_failed_messages_task(self, older_than_hours: int = 24) -> Dict[str, Any]:
    """
    Retry sending failed messages that haven't been retried recently
    
    Args:
        older_than_hours: Only retry messages that failed more than X hours ago
        
    Returns:
        Dict with retry results
    """
    db = get_db_session()
    
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        failed_messages = db.query(PatientMessage).filter(
            PatientMessage.status == MessageStatus.FAILED,
            PatientMessage.updated_at < cutoff_time
        ).limit(50).all()
        
        retried_count = 0
        for message in failed_messages:
            try:
                message.status = MessageStatus.PENDING
                message.error_message = None
                db.commit()
                send_message_task.delay(str(message.id))
                retried_count += 1
            except Exception as e:
                logger.error(f"Failed to retry message {message.id}: {e}")
                db.rollback()
        
        logger.info(f"Failed message retry: {retried_count} messages requeued")
        return {
            "status": "completed",
            "retried": retried_count,
            "total_failed": len(failed_messages)
        }
        
    except Exception as e:
        logger.error(f"Error in retry_failed_messages_task: {e}")
        raise self.retry(exc=e)
    
    finally:
        db.close()


@shared_task(bind=True)
def cleanup_old_messages_task(self, days_old: int = 90) -> Dict[str, Any]:
    """
    Clean up old processed messages to manage storage
    
    Args:
        days_old: Delete messages older than this many days
        
    Returns:
        Dict with cleanup results
    """
    db = get_db_session()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted_count = db.query(PatientMessage).filter(
            PatientMessage.status.in_([MessageStatus.SENT, MessageStatus.DELIVERED, MessageStatus.FAILED]),
            PatientMessage.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old messages")
        return {
            "status": "completed",
            "deleted": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_messages_task: {e}")
        db.rollback()
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()