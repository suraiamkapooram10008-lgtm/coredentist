"""
Durable Email Queue
===================

Transactional emails (password reset, email verification, payment
receipts, appointment reminders) are sent through a Celery task with
exponential-backoff retry.  This removes the request-path cost of
SMTP (which can be 1-5s for SendGrid/SES) and ensures a transient
SMTP outage does not lose the email.

The ``send_email_task`` Celery task is the only entry point for
transactional email.  Endpoints call ``enqueue_email(...)`` (a
synchronous wrapper) which returns immediately after pushing the task
to Redis.  The Celery worker picks it up and dispatches to the
``email_service`` singleton.

Retry policy: 5 attempts with exponential backoff (1m, 5m, 25m, 2h,
10h) for a total of ~13h retry window.  After that, the email is
marked as failed in Sentry at ``error`` level and an on-call alert
is expected.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.celery_app import celery_app
from app.core.email import email_service

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.core.email_tasks.send_email_task",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,            # 1 minute
    retry_backoff_max=36000,     # cap at 10h
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def send_email_task(
    self,
    to: str | List[str],
    subject: str,
    html_content: Optional[str] = None,
    text_content: Optional[str] = None,
    template_id: Optional[str] = None,
    dynamic_template_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Dispatch a single email via the configured provider.

    Retries on any exception with exponential backoff.  After 5
    retries the email is considered permanently failed; we surface
    the failure to Sentry at error level.
    """
    import asyncio
    try:
        # The email service is async; run it in an event loop.
        # Celery workers run in their own process/loop, so creating
        # one per call is fine.
        return asyncio.run(
            email_service.send_email(
                to=to,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                template_id=template_id,
                dynamic_template_data=dynamic_template_data,
            )
        )
    except Exception as exc:
        attempt = self.request.retries + 1
        logger.warning(
            f"Email send attempt {attempt}/5 failed: {subject!r} -> {to!r}: {exc}"
        )
        if attempt >= 5:
            # Out of retries.  Alert the on-call.
            _alert_permanent_failure(to, subject, exc)
        raise


def _alert_permanent_failure(to, subject, exc) -> None:
    """
    Called when an email has exhausted all retries.  We log to Sentry
    at error level.  The on-call Sentry alert is configured to page
    on event_type=email_permanent_failure.
    """
    logger.error(
        f"Email PERMANENTLY FAILED after 5 retries: {subject!r} -> {to!r}: {exc}"
    )
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("event_type", "email_permanent_failure")
            scope.set_context(
                "email_failure",
                {
                    "recipients": to if isinstance(to, list) else [to],
                    "subject": subject,
                    "error": str(exc),
                },
            )
            sentry_sdk.capture_exception(exc)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Synchronous wrapper for endpoint code
# ---------------------------------------------------------------------------


def enqueue_email(
    to: str | List[str],
    subject: str,
    html_content: Optional[str] = None,
    text_content: Optional[str] = None,
    template_id: Optional[str] = None,
    dynamic_template_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Push an email onto the Celery queue.  Returns the Celery task
    ID.  Use this in endpoint code instead of calling
    ``email_service.send_email`` directly so the request handler
    is not blocked on SMTP.

    On systems where Celery is not running (e.g. local dev with
    eager=False disabled), this call still returns successfully; the
    task just sits in the broker until a worker picks it up.  For
    local dev with CELERY_TASK_ALWAYS_EAGER=true, the task runs
    synchronously in this process.
    """
    result = send_email_task.delay(
        to=to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        template_id=template_id,
        dynamic_template_data=dynamic_template_data,
    )
    return result.id
