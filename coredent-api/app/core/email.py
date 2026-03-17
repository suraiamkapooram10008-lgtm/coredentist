"""
Email Service
SendGrid and AWS SES integration for transactional emails
"""

import os
import logging
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"
    CONSOLE = "console"  # For development


class EmailService:
    """
    Email service supporting multiple providers:
    - SendGrid
    - AWS SES
    - Console (development)
    """
    
    def __init__(self, provider: Optional[EmailProvider] = None):
        self.provider = provider or EmailProvider(
            os.getenv("EMAIL_PROVIDER", "console")
        )
        self.from_email = os.getenv("EMAIL_FROM", "noreply@coredent.app")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "CoreDent")
        
    async def send_email(
        self,
        to: str | List[str],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        template_id: Optional[str] = None,
        dynamic_template_data: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email using the configured provider
        """
        recipients = [to] if isinstance(to, str) else to
        
        email_data = {
            "from": f"{self.from_name} <{self.from_email}>",
            "to": recipients,
            "subject": subject,
            "html": html_content,
            "text": text_content,
            "attachments": attachments,
        }
        
        if self.provider == EmailProvider.SENDGRID:
            return await self._send_sendgrid(email_data, template_id, dynamic_template_data)
        elif self.provider == EmailProvider.AWS_SES:
            return await self._send_aws_ses(email_data)
        else:
            return await self._send_console(email_data)
    
    async def _send_sendgrid(
        self,
        email_data: Dict[str, Any],
        template_id: Optional[str],
        dynamic_template_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Send email via SendGrid"""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import (
                Mail, Email, To, Content, Attachment, FileContent, 
                FileName, FileType, Disposition
            )
            
            sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
            
            message = Mail(
                from_email=email_data["from"],
                to_emails=email_data["to"],
                subject=email_data["subject"],
            )
            
            if template_id:
                message.template_id = template_id
                message.dynamic_template_data = dynamic_template_data or {}
            
            if email_data.get("html"):
                message.html_content = email_data["html"]
            if email_data.get("text"):
                message.content = [
                    {"type": "text/plain", "value": email_data["text"]}
                ]
            
            response = sg.send(message)
            
            logger.info(f"SendGrid email sent successfully: {response.status_code}")
            return {
                "success": True,
                "provider": "sendgrid",
                "message_id": response.headers.get("x-message-id"),
                "status_code": response.status_code,
            }
        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            raise
    
    async def _send_aws_ses(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via AWS SES"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            ses_client = boto3.client(
                "ses",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-1"),
            )
            
            destination = {"ToAddresses": email_data["to"]}
            
            message = {
                "Subject": {"Data": email_data["subject"]},
                "Body": {},
            }
            
            if email_data.get("html"):
                message["Body"]["Html"] = {"Data": email_data["html"]}
            if email_data.get("text"):
                message["Body"]["Text"] = {"Data": email_data["text"]}
            
            response = ses_client.send_email(
                Source=email_data["from"],
                Destination=destination,
                Message=message,
            )
            
            logger.info(f"AWS SES email sent successfully")
            return {
                "success": True,
                "provider": "aws_ses",
                "message_id": response["MessageId"],
            }
        except ClientError as e:
            logger.error(f"AWS SES error: {str(e)}")
            raise
    
    async def _send_console(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log email to console (development)"""
        logger.info("=" * 50)
        logger.info(f"📧 EMAIL (Development Mode)")
        logger.info("=" * 50)
        logger.info(f"From: {email_data['from']}")
        logger.info(f"To: {', '.join(email_data['to'])}")
        logger.info(f"Subject: {email_data['subject']}")
        if email_data.get("text"):
            logger.info(f"Body: {email_data['text'][:200]}...")
        logger.info("=" * 50)
        
        return {
            "success": True,
            "provider": "console",
            "message_id": f"dev-{datetime.now().timestamp()}",
        }
    
    # Convenience methods for common emails
    
    async def send_welcome_email(self, to: str, first_name: str) -> Dict[str, Any]:
        """Send welcome email to new patients"""
        return await self.send_email(
            to=to,
            subject="Welcome to CoreDent!",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Welcome to CoreDent, {first_name}!</h1>
                    <p>Thank you for choosing CoreDent for your dental care needs.</p>
                    <p>We're excited to have you as a patient!</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        This email was sent by CoreDent Dental Practice Management
                    </p>
                </body>
            </html>
            """,
            text_content=f"Welcome to CoreDent, {first_name}! Thank you for choosing us.",
        )
    
    async def send_appointment_reminder(
        self,
        to: str,
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        dentist_name: str,
    ) -> Dict[str, Any]:
        """Send appointment reminder"""
        return await self.send_email(
            to=to,
            subject="Appointment Reminder - CoreDent",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Appointment Reminder</h1>
                    <p>Dear {patient_name},</p>
                    <p>This is a reminder about your upcoming dental appointment:</p>
                    <ul>
                        <li><strong>Date:</strong> {appointment_date}</li>
                        <li><strong>Time:</strong> {appointment_time}</li>
                        <li><strong>Dentist:</strong> {dentist_name}</li>
                    </ul>
                    <p>Please arrive 15 minutes early.</p>
                    <p>Need to reschedule? Please call us.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        CoreDent Dental Practice Management
                    </p>
                </body>
            </html>
            """,
        )
    
    async def send_appointment_confirmation(
        self,
        to: str,
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        procedure: str,
    ) -> Dict[str, Any]:
        """Send appointment confirmation"""
        return await self.send_email(
            to=to,
            subject="Appointment Confirmed - CoreDent",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Appointment Confirmed ✅</h1>
                    <p>Dear {patient_name},</p>
                    <p>Your appointment has been confirmed:</p>
                    <ul>
                        <li><strong>Date:</strong> {appointment_date}</li>
                        <li><strong>Time:</strong> {appointment_time}</li>
                        <li><strong>Procedure:</strong> {procedure}</li>
                    </ul>
                    <p>We look forward to seeing you!</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        CoreDent Dental Practice Management
                    </p>
                </body>
            </html>
            """,
        )
    
    async def send_insurance_claim_submitted(
        self,
        to: str,
        patient_name: str,
        claim_number: str,
        amount: float,
    ) -> Dict[str, Any]:
        """Send insurance claim submission notification"""
        return await self.send_email(
            to=to,
            subject=f"Insurance Claim Submitted - {claim_number}",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Insurance Claim Submitted</h1>
                    <p>Dear {patient_name},</p>
                    <p>Your insurance claim has been submitted:</p>
                    <ul>
                        <li><strong>Claim Number:</strong> {claim_number}</li>
                        <li><strong>Amount:</strong> ${amount:.2f}</li>
                    </ul>
                    <p>We'll notify you once we receive a response from your insurance.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        CoreDent Dental Practice Management
                    </p>
                </body>
            </html>
            """,
        )


# Singleton instance
email_service = EmailService()
