"""
Celery Configuration for CoreDent
Handles automated tasks like sending reminders
"""

from celery import Celery
from datetime import datetime, timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Celery configuration
celery_app = Celery(
    'coredent',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.core.tasks',
        'app.core.reminder_tasks',
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
}

logger.info("Celery app initialized with scheduled tasks")