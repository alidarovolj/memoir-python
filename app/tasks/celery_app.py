"""Celery application configuration"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "memoir",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.ai_tasks", "app.tasks.notification_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)

# Celery Beat Schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Check task reminders every hour
    'check-task-reminders': {
        'task': 'check_task_reminders',
        'schedule': crontab(minute=0),  # Every hour at minute 0
    },
    # Check pet health every 12 hours
    'check-pet-health': {
        'task': 'check_pet_health',
        'schedule': crontab(hour='*/12', minute=0),  # Every 12 hours
    },
    # Send throwback notifications every morning at 9:00 AM
    'send-throwback-notifications': {
        'task': 'send_throwback_notifications',
        'schedule': crontab(hour=9, minute=0),  # Every day at 9:00 AM
    },
}

