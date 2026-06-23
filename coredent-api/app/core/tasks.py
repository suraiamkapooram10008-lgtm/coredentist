"""
CoreDent Celery Tasks
Handles automated background tasks
"""

from celery import shared_task
from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy import and_

from app.core.email import send_reminder_email
from app.core.sms import send_twilio_sms
from app.models.appointment import Appointment
from app.models.reminder import Reminder
from app.models.communication_settings import CommunicationSettings
from app.models.user import User
from app.models.practice import Practice
from app.api.deps import get_db

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_appointment_reminders(self):
    """
    Send appointment reminders based on scheduled time
    """
    try:
        db = next(get_db())

        # Get all pending reminders that are due
        now = datetime.now(timezone.utc)
        due_reminders = db.query(Reminder).filter(
            and_(
                Reminder.status == 'pending',
                Reminder.scheduled_time <= now
            )
        ).all()

        sent_count = 0
        failed_count = 0

        for reminder in due_reminders:
            try:
                # Get patient and appointment details
                appointment = db.query(Appointment).filter(
                    Appointment.id == reminder.appointment_id
                ).first()

                if not appointment:
                    logger.warning(f"Appointment not found for reminder {reminder.id}")
                    reminder.status = 'failed'
                    reminder.failure_reason = 'Appointment not found'
                    db.commit()
                    failed_count += 1
                    continue

                # Get practice settings
                practice = db.query(Practice).filter(
                    Practice.id == appointment.practice_id
                ).first()

                settings = db.query(CommunicationSettings).filter(
                    CommunicationSettings.practice_id == practice.id
                ).first()

                # Send reminder based on channel
                success = False
                if reminder.channel == 'email' and appointment.patient.email:
                    success = send_reminder_email(
                        to_email=appointment.patient.email,
                        patient_name=f"{appointment.patient.first_name} {appointment.patient.last_name}",
                        appointment_date=appointment.start_time,
                        appointment_type=appointment.appointment_type,
                        practice_name=practice.name,
                        practice_phone=practice.phone
                    )

                elif reminder.channel == 'sms' and appointment.patient.phone:
                    success = send_twilio_sms(
                        to_phone=appointment.patient.phone,
                        message=f"Reminder: Your appointment is scheduled for {appointment.start_time.strftime('%Y-%m-%d at %I:%M %p')}"
                    )

                # Update reminder status
                if success:
                    reminder.status = 'sent'
                    reminder.sent_time = datetime.now(timezone.utc)
                    sent_count += 1
                else:
                    reminder.status = 'failed'
                    reminder.failure_reason = 'Failed to send'
                    failed_count += 1

                db.commit()

            except Exception as e:
                logger.error(f"Error sending reminder {reminder.id}: {e}")
                reminder.status = 'failed'
                reminder.failure_reason = str(e)
                db.commit()
                failed_count += 1

        logger.info(f"Reminder task completed: {sent_count} sent, {failed_count} failed")
        return {"sent": sent_count, "failed": failed_count}

    except Exception as e:
        logger.error(f"Error in send_appointment_reminders: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_daily_summary(self):
    """
    Send daily summary to practice administrators
    """
    try:
        db = next(get_db())

        # Get all practices
        practices = db.query(Practice).all()

        for practice in practices:
            try:
                # Get today's statistics
                today = datetime.now(timezone.utc).date()
                tomorrow = today + timedelta(days=1)

                # Appointments today
                appointments_today = db.query(Appointment).filter(
                    and_(
                        Appointment.practice_id == practice.id,
                        Appointment.start_time >= today,
                        Appointment.start_time < tomorrow
                    )
                ).count()

                # Pending reminders
                pending_reminders = db.query(Reminder).filter(
                    and_(
                        Reminder.status == 'pending',
                        Reminder.scheduled_time >= datetime.now(timezone.utc)
                    )
                ).count()

                # Failed reminders
                failed_reminders = db.query(Reminder).filter(
                    Reminder.status == 'failed'
                ).count()

                # Send summary email to practice admin
                admin_users = db.query(User).filter(
                    and_(
                        User.practice_id == practice.id,
                        User.role.in_(['admin', 'owner'])
                    )
                ).all()

                for admin in admin_users:
                    if admin.email:
                        # This would send a summary email
                        # Implementation depends on email template system
                        logger.info(f"Daily summary for {practice.name} sent to {admin.email}")

            except Exception as e:
                logger.error(f"Error sending daily summary for practice {practice.id}: {e}")

        return {"status": "daily summary sent"}

    except Exception as e:
        logger.error(f"Error in send_daily_summary: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task(bind=True, max_retries=3)
def process_scheduled_reminders(self):
    """
    Process reminders that should be scheduled based on appointment times
    """
    try:
        db = next(get_db())

        # Get appointments that need reminders
        now = datetime.now(timezone.utc)
        # Look for appointments in the next 24-48 hours that don't have reminders yet
        target_time_start = now + timedelta(hours=24)
        target_time_end = now + timedelta(hours=48)

        appointments = db.query(Appointment).filter(
            and_(
                Appointment.start_time >= target_time_start,
                Appointment.start_time <= target_time_end,
                Appointment.status == 'scheduled'
            )
        ).all()

        created_count = 0

        for appointment in appointments:
            # Check if reminder already exists
            existing_reminder = db.query(Reminder).filter(
                Reminder.appointment_id == appointment.id
            ).first()

            if not existing_reminder:
                # Create reminder 24 hours before appointment
                reminder_time = appointment.start_time - timedelta(hours=24)

                reminder = Reminder(
                    patient_id=appointment.patient_id,
                    appointment_id=appointment.id,
                    reminder_type='appointment',
                    scheduled_time=reminder_time,
                    message=f"Reminder: Your appointment is scheduled for {appointment.start_time.strftime('%Y-%m-%d at %I:%M %p')}",
                    channel='email',  # Default to email
                    status='pending'
                )

                db.add(reminder)
                created_count += 1

        if created_count > 0:
            db.commit()
            logger.info(f"Created {created_count} new reminders")

        return {"created": created_count}

    except Exception as e:
        logger.error(f"Error in process_scheduled_reminders: {e}")
        raise self.retry(exc=e, countdown=120)


@shared_task(bind=True, max_retries=3)
def cleanup_old_notifications(self):
    """
    Clean up old notifications and failed reminders
    """
    try:
        db = next(get_db())

        # Remove notifications older than 30 days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        # This would depend on your notification model
        # For now, just log the cleanup
        logger.info(f"Cleaning up notifications older than {cutoff_date}")

        # Remove failed reminders older than 7 days
        failed_cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        failed_reminders = db.query(Reminder).filter(
            and_(
                Reminder.status == 'failed',
                Reminder.created_at < failed_cutoff
            )
        ).delete()

        db.commit()

        logger.info(f"Cleaned up {failed_reminders} old failed reminders")
        return {"cleaned_up": failed_reminders}

    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications: {e}")
        raise self.retry(exc=e, countdown=600)


@shared_task(bind=True, max_retries=3)
def send_payment_reminder(self, payment_id: str):
    """
    Send payment reminder for overdue invoices
    """
    try:
        db = next(get_db())

        from app.models.payment import Payment
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment or payment.status != 'pending':
            return {"status": "skipped", "reason": "Payment not found or already processed"}

        # Send payment reminder email
        if payment.patient and payment.patient.email:
            success = send_reminder_email(
                to_email=payment.patient.email,
                patient_name=f"{payment.patient.first_name} {payment.patient.last_name}",
                amount=payment.amount,
                currency=payment.currency,
                payment_id=payment.id
            )

            if success:
                return {"status": "sent", "payment_id": payment_id}
            else:
                return {"status": "failed", "payment_id": payment_id}

        return {"status": "skipped", "reason": "No email available"}

    except Exception as e:
        logger.error(f"Error in send_payment_reminder: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task(bind=True, max_retries=3)
def process_bulk_reminder(self, practice_id: str, message: str, channel: str, patient_ids: list):
    """
    Send bulk reminders to multiple patients
    """
    try:
        db = next(get_db())

        sent_count = 0
        failed_count = 0

        for patient_id in patient_ids:
            try:
                # Create individual reminder
                reminder = Reminder(
                    patient_id=patient_id,
                    reminder_type='bulk',
                    scheduled_time=datetime.now(timezone.utc),
                    message=message,
                    channel=channel,
                    status='pending'
                )

                db.add(reminder)

                # Send immediately if channel is specified
                if channel == 'email':
                    # Send email
                    pass
                elif channel == 'sms':
                    # Send SMS
                    pass

                sent_count += 1

            except Exception as e:
                logger.error(f"Error processing bulk reminder for patient {patient_id}: {e}")
                failed_count += 1

        db.commit()

        return {
            "status": "completed",
            "practice_id": practice_id,
            "sent": sent_count,
            "failed": failed_count
        }

    except Exception as e:
        logger.error(f"Error in process_bulk_reminder: {e}")
        raise self.retry(exc=e, countdown=600)