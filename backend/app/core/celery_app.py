"""
Celery application configuration for background tasks
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "aurora_life",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.ml_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.analytics_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks schedule (Celery Beat)
celery_app.conf.beat_schedule = {
    "retrain-ml-models-daily": {
        "task": "app.tasks.ml_tasks.retrain_all_models",
        "schedule": 86400.0,  # Every 24 hours
    },
    "cleanup-old-data-weekly": {
        "task": "app.tasks.analytics_tasks.cleanup_old_data",
        "schedule": 604800.0,  # Every 7 days
    },
    "generate-daily-insights": {
        "task": "app.tasks.analytics_tasks.generate_daily_insights",
        "schedule": 86400.0,  # Every 24 hours at midnight
    },
}
