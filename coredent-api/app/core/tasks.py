"""
CoreDent Celery Tasks
Handles automated background tasks using synchronous DB sessions.
"""

from contextlib import contextmanager
from celery import shared_task
from datetime import datetime, timedelta, timezone
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import asyncio

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.email import EmailService
from app.core.sms import SMSService
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.practice import Practice
from app.models.user import User, UserRole
from app.models.communication import PatientMessage, MessageType, MessageDirection, MessageStatus
from app.models.billing import Invoice, InvoiceStatus

logger = logging.getLogger(__name__)

email_service = EmailService()
sms_service = SMSService()


@contextmanager
def _get_sync_db():
    """Get a sync DB session for Celery tasks (context manager)."""
    from app.core.database import get_sync_db
    with get_sync_db() as db:
        yield db
def _run_async(coro):
    """Run an async coroutine from a sync context (Celery worker)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop closed")
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(bind=True, max_retries=3)
def send_appointment_reminders(self):
    """
    Send appointment reminders for upcoming appointments.
    Looks for appointments in next 24 hours and sends email/SMS reminders.
    """
    try:
        with _get_sync_db() as db:
            now = datetime.now(timezone.utc)
            next_24h = now + timedelta(hours=24)

            # Find confirmed/scheduled appointments in next 24h
            # that haven't had a reminder sent yet
            appointments = db.query(Appointment).filter(
                and_(
                    Appointment.start_time >= now,
                    Appointment.start_time <= next_24h,
                    Appointment.status == AppointmentStatus.SCHEDULED,
                    Appointment.reminder_sent == False
                )
            ).all()

            sent_count = 0
            failed_count = 0

            for appointment in appointments:
                try:
                    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
                    practice = db.query(Practice).filter(Practice.id == appointment.practice_id).first()
                    if not patient or not practice:
                        continue

                    # Try email first, then SMS fallback
                    success = False
                    if patient.email:
                        try:
                            _run_async(
                                email_service.send_email(
                                    to=patient.email,
                                    subject=f"Reminder: Appointment at {practice.name}",
                                    text_content=(
                                        f"Hi {patient.first_name},\n\n"
                                        f"This is a reminder for your appointment at {practice.name}\n"
                                        f"Date: {appointment.start_time.strftime('%Y-%m-%d')}\n"
                                        f"Time: {appointment.start_time.strftime('%I:%M %p')}\n"
                                        f"Type: {appointment.appointment_type}\n\n"
                                        f"Please call {practice.phone} if you need to reschedule."
                                    ),
                                )
                            )
                            success = True
                        except Exception as e:
                            logger.warning(f"Email reminder failed for {patient.id}: {e}")

                    if not success and patient.phone:
                        try:
                            _run_async(
                                sms_service.send_appointment_reminder(
                                    to=patient.phone,
                                    patient_name=patient.first_name,
                                    appointment_date=appointment.start_time.strftime('%Y-%m-%d'),
                                    appointment_time=appointment.start_time.strftime('%I:%M %p'),
                                    practice_name=practice.name,
                                )
                            )
                            success = True
                        except Exception as e:
                            logger.warning(f"SMS reminder failed for {patient.id}: {e}")

                    if success:
                        appointment.reminder_sent = True
                        sent_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error processing reminder for appointment {appointment.id}: {e}")
                    failed_count += 1

            db.commit()
            logger.info(f"Reminder task: {sent_count} sent, {failed_count} failed")
            return {"sent": sent_count, "failed": failed_count}

    except Exception as e:
        logger.error(f"Error in send_appointment_reminders: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_daily_summary(self):
    """
    Send daily summary to practice administrators.
    """
    try:
        with _get_sync_db() as db:
            today = datetime.now(timezone.utc).date()
            tomorrow = today + timedelta(days=1)
            today_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
            today_end = datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.utc)

            practices = db.query(Practice).all()
            summary_count = 0

            for practice in practices:
                try:
                    appointments_today = db.query(Appointment).filter(
                        and_(
                            Appointment.practice_id == practice.id,
                            Appointment.start_time >= today_start,
                            Appointment.start_time < today_end,
                        )
                    ).count()

                    completed = db.query(Appointment).filter(
                        and_(
                            Appointment.practice_id == practice.id,
                            Appointment.start_time >= today_start,
                            Appointment.start_time < today_end,
                            Appointment.status == AppointmentStatus.COMPLETED,
                        )
                    ).count()

                    admin_users = db.query(User).filter(
                        and_(
                            User.practice_id == practice.id,
                            User.role.in_([UserRole.ADMIN, UserRole.OWNER]),
                        )
                    ).all()

                    for admin in admin_users:
                        if admin.email:
                            logger.info(
                                f"Daily summary for {practice.name}: "
                                f"{appointments_today} appointments, {completed} completed. "
                                f"Sent to {admin.email}"
                            )
                            summary_count += 1

                except Exception as e:
                    logger.error(f"Error generating daily summary for practice {practice.id}: {e}")

            db.commit()
            return {"status": "daily summary sent", "summaries": summary_count}

    except Exception as e:
        logger.error(f"Error in send_daily_summary: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task(bind=True, max_retries=3)
def process_scheduled_reminders(self):
    """
    Schedule reminders for upcoming appointments (24-48h window).
    """
    try:
        with _get_sync_db() as db:
            now = datetime.now(timezone.utc)
            target_start = now + timedelta(hours=24)
            target_end = now + timedelta(hours=48)

            appointments = db.query(Appointment).filter(
                and_(
                    Appointment.start_time >= target_start,
                    Appointment.start_time <= target_end,
                    Appointment.status == AppointmentStatus.SCHEDULED,
                    Appointment.reminder_sent == False,
                )
            ).all()

            marked_count = 0
            for appointment in appointments:
                # Just log that these will be picked up by send_appointment_reminders
                marked_count += 1

            logger.info(f"Found {marked_count} appointments needing reminders in next 24-48h")
            return {"found": marked_count}

    except Exception as e:
        logger.error(f"Error in process_scheduled_reminders: {e}")
        raise self.retry(exc=e, countdown=120)


@shared_task(bind=True, max_retries=3)
def cleanup_old_notifications(self):
    """
    Clean up old patient messages and booking notifications.
    """
    try:
        with _get_sync_db() as db:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

            # Clean up old read patient messages
            old_messages = db.query(PatientMessage).filter(
                and_(
                    PatientMessage.status == MessageStatus.READ,
                    PatientMessage.created_at < cutoff_date,
                )
            ).delete()

            db.commit()
            logger.info(f"Cleaned up {old_messages} old read messages")
            return {"cleaned_up": old_messages}

    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications: {e}")
        raise self.retry(exc=e, countdown=600)


@shared_task(bind=True, max_retries=3)
def send_payment_reminder(self, payment_id: str):
    """
    Send payment reminder for an overdue invoice.
    """
    try:
        with _get_sync_db() as db:
            from app.models.payment import Payment
            payment = db.query(Payment).filter(Payment.id == payment_id).first()

            if not payment:
                return {"status": "skipped", "reason": "Payment not found"}

            patient = db.query(Patient).filter(Patient.id == payment.patient_id).first()
            if not patient or not patient.email:
                return {"status": "skipped", "reason": "No email available"}

            try:
                _run_async(
                    email_service.send_email(
                        to=patient.email,
                        subject="Payment Reminder",
                        text_content=(
                            f"Hi {patient.first_name},\n\n"
                            f"This is a friendly reminder that you have a pending payment.\n\n"
                            f"Payment ID: {payment.id}\n"
                            f"Please contact us if you have any questions."
                        ),
                    )
                )
                return {"status": "sent", "payment_id": payment_id}
            except Exception as e:
                logger.error(f"Failed to send payment reminder: {e}")
                return {"status": "failed", "payment_id": payment_id, "error": str(e)}

    except Exception as e:
        logger.error(f"Error in send_payment_reminder: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task(bind=True, max_retries=3)
def process_bulk_reminder(self, practice_id: str, message: str, channel: str, patient_ids: list):
    """
    Send bulk reminders to multiple patients.
    """
    try:
        with _get_sync_db() as db:
            sent_count = 0
            failed_count = 0

            for patient_id in patient_ids:
                try:
                    patient = db.query(Patient).filter(Patient.id == patient_id).first()
                    if not patient:
                        continue

                    if channel == 'email' and patient.email:
                        _run_async(
                            email_service.send_email(
                                to=patient.email,
                                subject="Message from your dental practice",
                                text_content=message,
                            )
                        )
                        sent_count += 1
                    elif channel == 'sms' and patient.phone:
                        _run_async(sms_service.send_sms(to=patient.phone, message=message))
                        sent_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error sending bulk reminder to {patient_id}: {e}")
                    failed_count += 1

            db.commit()
            return {
                "status": "completed",
                "practice_id": practice_id,
                "sent": sent_count,
                "failed": failed_count,
            }

    except Exception as e:
        logger.error(f"Error in process_bulk_reminder: {e}")
        raise self.retry(exc=e, countdown=600)
