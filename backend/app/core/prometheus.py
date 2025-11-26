"""
Prometheus metrics collection for AURORA_LIFE
"""
from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Database metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

# ML model metrics
ml_prediction_duration_seconds = Histogram(
    'ml_prediction_duration_seconds',
    'ML model prediction duration',
    ['model_type']
)

ml_predictions_total = Counter(
    'ml_predictions_total',
    'Total ML predictions',
    ['model_type', 'status']
)

# Celery task metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration',
    ['task_name']
)

# User metrics
users_active_total = Gauge(
    'users_active_total',
    'Total active users'
)

events_created_total = Counter(
    'events_created_total',
    'Total life events created',
    ['event_type']
)

# Application info
app_info = Info('app_info', 'Application information')
app_info.info({
    'version': '1.0.0',
    'environment': 'production'
})


def track_request_metrics(method: str, endpoint: str):
    """Decorator to track HTTP request metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 200

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

        return wrapper
    return decorator


def track_ml_prediction(model_type: str):
    """Decorator to track ML prediction metrics."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                ml_predictions_total.labels(
                    model_type=model_type,
                    status=status
                ).inc()
                ml_prediction_duration_seconds.labels(
                    model_type=model_type
                ).observe(duration)

        return wrapper
    return decorator
