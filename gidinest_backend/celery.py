"""
Celery configuration for GidiNest backend.

This module sets up Celery for async task processing and periodic tasks.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gidinest_backend.settings')

app = Celery('gidinest_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


# Periodic task schedule
app.conf.beat_schedule = {
    'sync-embedly-verifications-every-6-hours': {
        'task': 'account.tasks.sync_embedly_verifications_task',
        'schedule': crontab(hour='*/6'),  # Run every 6 hours
        # Alternative schedules:
        # crontab(minute=0, hour='*/6')  # Every 6 hours at the top of the hour
        # crontab(minute=0, hour=2)      # Daily at 2 AM
        # crontab(minute=0, hour='*/12') # Every 12 hours
    },
    'unlock-matured-savings-goals-daily': {
        'task': 'savings.tasks.unlock_matured_goals',
        'schedule': crontab(minute=0, hour=0),  # Run daily at midnight UTC
    },
    'calculate-savings-interest-daily': {
        'task': 'savings.tasks.calculate_interest_for_goals',
        'schedule': crontab(minute=30, hour=0),  # Run daily at 12:30 AM UTC
    },
}

# Optional: Configure timezone for scheduled tasks
app.conf.timezone = 'UTC'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    import logging; logging.getLogger(__name__).info(f'Request: {self.request!r}')
