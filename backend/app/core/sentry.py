"""
Sentry error tracking integration
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

from app.core.config import settings


def init_sentry():
    """
    Initialize Sentry error tracking.

    Features:
    - FastAPI integration
    - SQLAlchemy query tracking
    - Redis operation tracking
    - Celery task tracking
    - Custom tags and context
    """
    if not getattr(settings, 'SENTRY_DSN', None):
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=getattr(settings, 'APP_ENV', 'development'),
        release=getattr(settings, 'APP_VERSION', '1.0.0'),
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # 10% for profiling
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
        ],
        # Set custom tags
        before_send=add_custom_context,
    )


def add_custom_context(event, hint):
    """Add custom context to Sentry events."""
    # Add custom tags
    event.setdefault('tags', {})
    event['tags']['service'] = 'aurora-life-api'

    # Add user context if available
    # This will be populated by middleware

    return event


def capture_exception(exception: Exception, **kwargs):
    """
    Capture exception with custom context.

    Args:
        exception: Exception to capture
        **kwargs: Additional context (tags, extra data)
    """
    with sentry_sdk.push_scope() as scope:
        # Add custom tags
        for key, value in kwargs.get('tags', {}).items():
            scope.set_tag(key, value)

        # Add extra context
        for key, value in kwargs.get('extra', {}).items():
            scope.set_context(key, value)

        sentry_sdk.capture_exception(exception)
