"""
Celery Configuration for CoreDent
Handles automated tasks like sending reminders
"""

from celery import Celery
from datetime import timedelta
import logging

from app.core.config_simple import settings

logger = logging.getLogger(__name__)

# Celery configuration
celery_app = Celery(
    'coredent',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.core.tasks',
        'app.core.reminder_tasks',
        'app.core.email_tasks',
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minute timeout
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Send appointment reminders every 15 minutes
    'send-appointment-reminders': {
        'task': 'app.core.tasks.send_appointment_reminders',
        'schedule': timedelta(minutes=15),
    },
    # Send daily summary
    'send-daily-summary': {
        'task': 'app.core.tasks.send_daily_summary',
        'schedule': timedelta(hours=24),
        'options': {'expires': 3600}
    },
    # Process scheduled reminders
    'process-scheduled-reminders': {
        'task': 'app.core.tasks.process_scheduled_reminders',
        'schedule': timedelta(minutes=5),
    },
    # Clean up old notifications
    'cleanup_old_notifications': {
        'task': 'app.core.tasks.cleanup_old_notifications',
        'schedule': timedelta(hours=1),
    },
    # Process scheduled messages every minute
    'process-scheduled-messages': {
        'task': 'app.core.communication_tasks.process_scheduled_messages_task',
        'schedule': timedelta(minutes=1),
    },
    # Retry failed messages every 5 minutes
    'retry-failed-messages': {
        'task': 'app.core.communication_tasks.retry_failed_messages_task',
        'schedule': timedelta(minutes=5),
    },
}

celery_app.conf.task_routes = {
    'app.core.tasks.*': {'queue': 'default'},
    'app.core.communication_tasks.*': {'queue': 'communications'},
    'app.core.reminder_tasks.*': {'queue': 'reminders'},
}

logger.info("Celery app initialized with scheduled tasks")