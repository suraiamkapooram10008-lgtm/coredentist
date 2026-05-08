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

    # ==================== Subscription Email Templates ====================

    async def send_subscription_welcome(
        self,
        to: str,
        customer_name: str,
        plan_name: str,
        amount: float,
        interval: str,
        trial_end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send welcome email for new subscription"""
        trial_text = (
            f"<p>Your free trial ends on <strong>{trial_end_date}</strong>. "
            f"You will be charged automatically after the trial period.</p>"
            if trial_end_date
            else "<p>Your subscription is now active.</p>"
        )
        return await self.send_email(
            to=to,
            subject=f"Welcome to {plan_name} - CoreDent",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                        <h1 style="color: white; margin: 0;">Welcome to CoreDent! 🎉</h1>
                    </div>
                    <div style="padding: 30px;">
                        <p>Dear {customer_name},</p>
                        <p>Thank you for subscribing to <strong>{plan_name}</strong>!</p>
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0;">Subscription Details</h3>
                            <ul style="list-style: none; padding: 0;">
                                <li style="padding: 8px 0;"><strong>Plan:</strong> {plan_name}</li>
                                <li style="padding: 8px 0;"><strong>Amount:</strong> ${amount:.2f}/{interval}</li>
                                <li style="padding: 8px 0;"><strong>Status:</strong> <span style="color: #28a745;">Active</span></li>
                            </ul>
                        </div>
                        {trial_text}
                        <p>You can manage your subscription anytime from your account settings.</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            CoreDent Dental Practice Management<br>
                            If you have any questions, please contact support.
                        </p>
                    </div>
                </body>
            </html>
            """,
            text_content=f"Welcome to CoreDent! You've subscribed to {plan_name} at ${amount:.2f}/{interval}.",
        )

    async def send_payment_receipt(
        self,
        to: str,
        customer_name: str,
        amount: float,
        invoice_number: str,
        payment_date: str,
        plan_name: str,
    ) -> Dict[str, Any]:
        """Send payment receipt email"""
        return await self.send_email(
            to=to,
            subject=f"Payment Receipt - Invoice {invoice_number}",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #28a745; padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">Payment Successful ✅</h1>
                    </div>
                    <div style="padding: 30px;">
                        <p>Dear {customer_name},</p>
                        <p>We've received your payment. Here's your receipt:</p>
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0;">Receipt Details</h3>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr><td style="padding: 8px 0;"><strong>Invoice Number:</strong></td><td>{invoice_number}</td></tr>
                                <tr><td style="padding: 8px 0;"><strong>Amount Paid:</strong></td><td style="color: #28a745; font-weight: bold;">${amount:.2f}</td></tr>
                                <tr><td style="padding: 8px 0;"><strong>Payment Date:</strong></td><td>{payment_date}</td></tr>
                                <tr><td style="padding: 8px 0;"><strong>Plan:</strong></td><td>{plan_name}</td></tr>
                            </table>
                        </div>
                        <p>Thank you for your payment. Your subscription remains active.</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            CoreDent Dental Practice Management
                        </p>
                    </div>
                </body>
            </html>
            """,
            text_content=f"Payment received: ${amount:.2f} for invoice {invoice_number}. Thank you!",
        )

    async def send_payment_failed(
        self,
        to: str,
        customer_name: str,
        amount: float,
        error_message: str,
        retry_date: str,
        attempt_number: int,
        max_attempts: int,
    ) -> Dict[str, Any]:
        """Send payment failure notification (dunning email)"""
        urgency_color = "#dc3545" if attempt_number >= 3 else "#ffc107"
        return await self.send_email(
            to=to,
            subject=f"⚠️ Payment Failed - Action Required",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: {urgency_color}; padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">Payment Failed ⚠️</h1>
                    </div>
                    <div style="padding: 30px;">
                        <p>Dear {customer_name},</p>
                        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0;"><strong>Important:</strong> We were unable to process your subscription payment.</p>
                        </div>
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <table style="width: 100%;">
                                <tr><td style="padding: 8px 0;"><strong>Amount:</strong></td><td>${amount:.2f}</td></tr>
                                <tr><td style="padding: 8px 0;"><strong>Attempt:</strong></td><td>{attempt_number} of {max_attempts}</td></tr>
                                <tr><td style="padding: 8px 0;"><strong>Next Retry:</strong></td><td>{retry_date}</td></tr>
                                <tr><td style="padding: 8px 0;"><strong>Error:</strong></td><td style="color: #dc3545;">{error_message}</td></tr>
                            </table>
                        </div>
                        <p><strong>What you need to do:</strong></p>
                        <ol>
                            <li>Check your payment method is still valid</li>
                            <li>Ensure sufficient funds are available</li>
                            <li>Update your payment method in account settings if needed</li>
                        </ol>
                        <p style="color: #666;">If we cannot process payment after {max_attempts} attempts, your subscription will be canceled.</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            CoreDent Dental Practice Management
                        </p>
                    </div>
                </body>
            </html>
            """,
            text_content=f"Payment failed: ${amount:.2f}. Attempt {attempt_number}/{max_attempts}. Next retry: {retry_date}. Error: {error_message}",
        )

    async def send_trial_expiring(
        self,
        to: str,
        customer_name: str,
        plan_name: str,
        trial_end_date: str,
        days_remaining: int,
        amount: float,
        interval: str,
    ) -> Dict[str, Any]:
        """Send trial expiration warning email"""
        return await self.send_email(
            to=to,
            subject=f"Your {plan_name} Trial Ends in {days_remaining} Days",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center;">
                        <h1 style="color: white; margin: 0;">Trial Ending Soon ⏰</h1>
                    </div>
                    <div style="padding: 30px;">
                        <p>Dear {customer_name},</p>
                        <p>Your free trial of <strong>{plan_name}</strong> is ending soon!</p>
                        <div style="background: #e7f3ff; border-left: 4px solid #0066cc; padding: 20px; margin: 20px 0;">
                            <h3 style="margin-top: 0;">Trial Details</h3>
                            <ul style="list-style: none; padding: 0;">
                                <li style="padding: 8px 0;"><strong>Days Remaining:</strong> {days_remaining}</li>
                                <li style="padding: 8px 0;"><strong>Trial Ends:</strong> {trial_end_date}</li>
                                <li style="padding: 8px 0;"><strong>After Trial:</strong> ${amount:.2f}/{interval}</li>
                            </ul>
                        </div>
                        <p><strong>What happens next?</strong></p>
                        <ul>
                            <li>Your subscription will automatically convert to a paid plan</li>
                            <li>Your payment method will be charged ${amount:.2f}</li>
                            <li>You'll continue to have full access to all features</li>
                        </ul>
                        <p>No action is needed - we'll handle everything automatically!</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            CoreDent Dental Practice Management
                        </p>
                    </div>
                </body>
            </html>
            """,
            text_content=f"Your {plan_name} trial ends in {days_remaining} days. After trial: ${amount:.2f}/{interval}.",
        )

    async def send_subscription_canceled(
        self,
        to: str,
        customer_name: str,
        plan_name: str,
        cancellation_date: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send subscription cancellation confirmation"""
        reason_text = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""
        return await self.send_email(
            to=to,
            subject=f"Subscription Canceled - {plan_name}",
            html_content=f"""
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #6c757d; padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">Subscription Canceled</h1>
                    </div>
                    <div style="padding: 30px;">
                        <p>Dear {customer_name},</p>
                        <p>Your subscription to <strong>{plan_name}</strong> has been canceled.</p>
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <ul style="list-style: none; padding: 0;">
                                <li style="padding: 8px 0;"><strong>Cancellation Date:</strong> {cancellation_date}</li>
                                <li style="padding: 8px 0;"><strong>Access Until:</strong> End of current billing period</li>
                            </ul>
                        </div>
                        {reason_text}
                        <p>We're sorry to see you go! If you change your mind, you can resubscribe anytime.</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="color: #666; font-size: 12px;">
                            CoreDent Dental Practice Management
                        </p>
                    </div>
                </body>
            </html>
            """,
            text_content=f"Your {plan_name} subscription has been canceled. Access continues until end of billing period.",
        )


# Singleton instance
email_service = EmailService()
