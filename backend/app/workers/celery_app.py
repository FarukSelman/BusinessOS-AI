"""
Celery application.

Start (from backend/, virtualenv active; start-dev.ps1 does this):

    celery -A app.workers.celery_app worker --pool=solo --loglevel=info
    celery -A app.workers.celery_app beat --loglevel=info

--pool=solo is required on Windows. Redis comes from infrastructure/docker-compose.yml.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "businessos",
    broker=settings.CELERY_BROKER_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    timezone=settings.APP_TIMEZONE,
    enable_utc=True,
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
    beat_schedule={
        "send-due-appointment-reminders": {
            "task": "reminders.send_due_reminders",
            "schedule": float(settings.REMINDER_SCAN_INTERVAL_SECONDS),
            # A scan that could not start in time is dropped; the next one covers it.
            "options": {"expires": float(settings.REMINDER_SCAN_INTERVAL_SECONDS)},
        },
        # Dashboard "AI İçgörüleri" for every business, at night (APP_TIMEZONE).
        "generate-business-insights-nightly": {
            "task": "insights.generate_all",
            "schedule": crontab(hour=3, minute=0),
            "options": {"expires": 6 * 3600.0},
        },
    },
)
