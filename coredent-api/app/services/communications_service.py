"""
Communications Engineering Service
Handles Twilio integration (Two-way SMS) and the Automated Recall Engine.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging
import os
import time

from app.models.practice import Practice
from app.models.patient import Patient, PatientStatus
from app.models.appointment import Appointment, AppointmentStatus, AppointmentTypeEnum
from app.models.communication import (
    PatientMessage, MessageTemplate, ReminderSchedule,
    Conversation, ConversationMessage, MessageType, MessageStatus, MessageDirection,
    ReminderType
)

logger = logging.getLogger(__name__)

class CommunicationsEngine:
    """Core Engine for Automated Reminders, Recalls, and Two-Way SMS"""

    def __init__(self, db: Session):
        self.db = db
        # In a real system, you would initialize twilio_client here:
        # self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def _replace_variables(self, template: str, context: dict) -> str:
        """Replace [variable] placeholders in template string"""
        result = template
        for key, value in context.items():
            result = result.replace(f"[{key}]", str(value or ''))
        return result

    def send_sms(self, to_phone: str, body: str, practice: Practice) -> Dict[str, Any]:
        """Send SMS via Twilio and fail closed when the provider is unavailable."""
        if not to_phone:
            return {"status": "failed", "error": "No phone number provided"}

        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        from_number = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
        if not account_sid or not auth_token or not from_number:
            logger.error("SMS delivery unavailable: Twilio is not fully configured")
            return {"status": "failed", "error": "SMS provider is not configured"}

        try:
            from twilio.rest import Client
            message = Client(account_sid, auth_token).messages.create(
                body=body,
                from_=from_number,
                to=to_phone,
            )
            return {"status": "sent", "external_id": message.sid}
        except Exception as exc:
            logger.error("Twilio SMS delivery failed: %s", exc)
            return {"status": "failed", "error": "SMS delivery failed"}

    def send_sms_with_retry(self, to_phone: str, body: str, practice: Practice, retries: int = 3, backoff: float = 0.5) -> Dict[str, Any]:
        """Send SMS with simple retry/backoff for transient failures"""
        attempt = 0
        while attempt <= retries:
            result = self.send_sms(to_phone, body, practice)
            if result.get("status") != "failed":
                return result
            attempt += 1
            if attempt <= retries:
                time.sleep(backoff * attempt)
        return result

    def process_automated_recalls(self):
        """
        Automated Recall System Engine
        Runs daily. Finds patients due for hygiene recalls and sends SMS/Email.
        """
        logger.info("Starting Automated Recall Engine...")
        now = datetime.now(timezone.utc)

        # 1. Get all active practices
        practices = self.db.query(Practice).filter(Practice.is_active == True).all()

        for practice in practices:
            # 2. Get active active recall schedules for this practice
            schedules = self.db.query(ReminderSchedule).filter(
                and_(
                    ReminderSchedule.practice_id == practice.id,
                    ReminderSchedule.is_active == True,
                    ReminderSchedule.reminder_type == ReminderType.RECALL
                )
            ).all()

            for schedule in schedules:
                if not schedule.template_id:
                    continue

                template = self.db.query(MessageTemplate).get(schedule.template_id)
                if not template:
                    continue

                # Logic: Find patients whose LAST completed hygiene appointment was X days ago
                # and who do NOT have a future matching appointment.

                # Lookback date
                target_date = now - timedelta(days=schedule.days_before) # Actually for recalls, days_before is positive "days since last visit"
                target_date_start = target_date.replace(hour=0, minute=0, second=0)
                target_date_end = target_date.replace(hour=23, minute=59, second=59)

                # Complex query simplified for demo:
                # Find appointments that were completed on target_date that are CLEANING/EXAM
                last_appointments = self.db.query(Appointment).filter(
                    and_(
                        Appointment.practice_id == practice.id,
                        Appointment.status == AppointmentStatus.COMPLETED,
                        Appointment.appointment_type.in_([AppointmentTypeEnum.CLEANING, AppointmentTypeEnum.EXAM]),
                        Appointment.end_time >= target_date_start,
                        Appointment.end_time <= target_date_end
                    )
                ).all()

                for apt in last_appointments:
                    patient = self.db.query(Patient).get(apt.patient_id)
                    if not patient or patient.status != PatientStatus.ACTIVE:
                        continue

                    # Check if they already have a future appointment schedule
                    future_apt = self.db.query(Appointment).filter(
                        and_(
                            Appointment.patient_id == patient.id,
                            Appointment.start_time > now,
                            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
                        )
                    ).first()

                    if future_apt:
                        continue # Already scheduled, skip recall

                    # Send Recall Message!
                    context = {
                        "patient_name": patient.first_name,
                        "practice_name": practice.name,
                        "last_visit_date": apt.start_time.strftime("%B %d, %Y") if apt.start_time else "recently",
                        "booking_link": f"https://yourdomain.com/book/{practice.slug}" if hasattr(practice, 'slug') else ""
                    }

                    body = self._replace_variables(template.content, context)

                    try:
                        # Record message
                        msg = PatientMessage(
                            practice_id=practice.id,
                            patient_id=patient.id,
                            template_id=template.id,
                            message_type=template.message_type,
                            direction=MessageDirection.OUTBOUND,
                            status=MessageStatus.PENDING,
                            content=body,
                            recipient_phone=patient.phone,
                            recipient_email=patient.email,
                            sent_at=now,
                            category="recall"
                        )

                        if template.message_type == MessageType.SMS:
                            result = self.send_sms_with_retry(patient.phone, body, practice)
                            if result.get("status") == "failed":
                                msg.status = MessageStatus.FAILED
                                msg.error_message = result.get("error")
                            else:
                                msg.status = MessageStatus.SENT
                                msg.external_id = result.get("external_id")
                                msg.sent_at = now
                        else:
                            msg.status = MessageStatus.FAILED
                            msg.error_message = "Email recall delivery is not configured"

                        self.db.add(msg)
                        self.db.commit()
                        logger.info(f"Recall sent to {patient.id} for practice {practice.name}")
                    except Exception as e:
                        self.db.rollback()
                        logger.error(f"Failed to send recall to {patient.id}: {str(e)}")

    def handle_inbound_sms(self, from_phone: str, to_phone: str, body: str, external_id: str):
        """
        Two-Way SMS Webhook Handler
        Parses inbound SMS from Twilio and routes it to the correct patient Conversation.
        """
        now = datetime.now(timezone.utc)

        # Clean phone number
        cleaned_phone = from_phone[-10:] if len(from_phone) >= 10 else from_phone

        # 1. Match phone number to a patient
        patient = self.db.query(Patient).filter(
            func.lower(Patient.phone).like(f"%{cleaned_phone}%")
        ).first()

        if not patient:
            logger.warning(f"Inbound SMS from unknown number: {from_phone}")
            return False

        practice_id = patient.practice_id

        # 2. Add to existing Conversation or create a new one
        conversation = self.db.query(Conversation).filter(
            and_(
                Conversation.patient_id == patient.id,
                Conversation.channel == MessageType.SMS,
                Conversation.status == 'active'
            )
        ).first()

        if not conversation:
            conversation = Conversation(
                practice_id=practice_id,
                patient_id=patient.id,
                channel=MessageType.SMS,
                status='active',
                last_message_at=now,
                last_message_preview=body[:255],
                unread_count=1
            )
            self.db.add(conversation)
            self.db.flush()
        else:
            conversation.last_message_at = now
            conversation.last_message_preview = body[:255]
            conversation.unread_count += 1

        # 3. Save ConversationMessage
        conv_msg = ConversationMessage(
            conversation_id=conversation.id,
            sender_type="patient",
            content=body,
            external_id=external_id,
            is_read=False
        )
        self.db.add(conv_msg)

        # 4. Save to PatientMessage audit log
        pat_msg = PatientMessage(
            practice_id=practice_id,
            patient_id=patient.id,
            message_type=MessageType.SMS,
            direction=MessageDirection.INBOUND,
            status=MessageStatus.DELIVERED,
            content=body,
            recipient_phone=to_phone,
            delivered_at=now
        )
        self.db.add(pat_msg)

        self.db.commit()
        return True
