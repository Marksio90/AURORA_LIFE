"""
OpenTelemetry distributed tracing configuration.

Provides:
- Request tracing across services
- Database query tracing
- Redis operation tracing
- External API call tracing
- Custom span creation
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.trace import Status, StatusCode
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_tracing(app):
    """
    Configure OpenTelemetry tracing for the application.

    Call this in main.py:
        from app.core.tracing import setup_tracing
        setup_tracing(app)
    """
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry tracing is disabled")
        return

    # Create resource with service info
    resource = Resource.create({
        "service.name": "aurora-life-api",
        "service.version": settings.VERSION,
        "deployment.environment": settings.ENVIRONMENT,
    })

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Configure OTLP exporter (to Jaeger, Tempo, etc.)
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_ENDPOINT,
        insecure=settings.ENVIRONMENT != "production"
    )

    # Add batch span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    logger.info("Instrumented FastAPI for tracing")

    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    logger.info("Instrumented SQLAlchemy for tracing")

    # Instrument Redis
    RedisInstrumentor().instrument()
    logger.info("Instrumented Redis for tracing")

    # Instrument HTTPX (for external API calls)
    HTTPXClientInstrumentor().instrument()
    logger.info("Instrumented HTTPX for tracing")

    logger.info(
        f"OpenTelemetry tracing configured. "
        f"Exporting to {settings.OTEL_EXPORTER_ENDPOINT}"
    )


# Get tracer for custom spans
tracer = trace.get_tracer(__name__)


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    record_exception: bool = True
):
    """
    Context manager for creating custom trace spans.

    Usage:
        with trace_span("calculate_energy_prediction", {"user_id": user.id}):
            prediction = model.predict(features)

        # Or with async
        async with trace_span("fetch_user_events"):
            events = await db.query(Event).filter_by(user_id=user_id).all()
    """
    with tracer.start_as_current_span(name) as span:
        # Add attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))

        try:
            yield span
        except Exception as e:
            if record_exception:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        else:
            span.set_status(Status(StatusCode.OK))


def add_span_attribute(key: str, value: Any):
    """Add attribute to current span."""
    span = trace.get_current_span()
    if span:
        span.set_attribute(key, str(value))


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Add event to current span."""
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


# Decorators for automatic tracing
from functools import wraps
from typing import Callable


def traced(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator for automatic function tracing.

    Usage:
        @traced("calculate_life_score")
        def calculate_life_score(user_id: str) -> float:
            ...

        @traced(attributes={"model": "energy"})
        async def predict_energy(features):
            ...
    """
    def decorator(func: Callable):
        span_name = name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_span(span_name, attributes):
                return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_span(span_name, attributes):
                return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Service-specific tracing helpers
class MLTracing:
    """Tracing helpers for ML operations."""

    @staticmethod
    def trace_prediction(model_type: str, user_id: str):
        """Trace ML prediction."""
        return trace_span(
            f"ml.predict.{model_type}",
            attributes={
                "ml.model_type": model_type,
                "ml.user_id": user_id
            }
        )

    @staticmethod
    def trace_training(model_type: str, dataset_size: int):
        """Trace ML training."""
        return trace_span(
            f"ml.train.{model_type}",
            attributes={
                "ml.model_type": model_type,
                "ml.dataset_size": dataset_size
            }
        )


class DBTracing:
    """Tracing helpers for database operations."""

    @staticmethod
    def trace_query(operation: str, table: str):
        """Trace database query."""
        return trace_span(
            f"db.{operation}",
            attributes={
                "db.operation": operation,
                "db.table": table
            }
        )


class APITracing:
    """Tracing helpers for external API calls."""

    @staticmethod
    def trace_api_call(provider: str, endpoint: str):
        """Trace external API call."""
        return trace_span(
            f"api.{provider}",
            attributes={
                "api.provider": provider,
                "api.endpoint": endpoint
            }
        )


# Example usage:
"""
# In ML model prediction
from app.core.tracing import MLTracing

async def predict_energy(user_id: str):
    with MLTracing.trace_prediction("energy", user_id):
        features = await get_features(user_id)
        prediction = model.predict(features)
        return prediction

# In database service
from app.core.tracing import DBTracing

async def get_user_events(user_id: str):
    with DBTracing.trace_query("select", "events"):
        events = await db.query(Event).filter_by(user_id=user_id).all()
        return events

# In external API call
from app.core.tracing import APITracing

async def generate_insight(prompt: str):
    with APITracing.trace_api_call("openai", "chat/completions"):
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response

# Custom span with decorator
from app.core.tracing import traced

@traced("calculate_life_score")
async def calculate_life_score(user_id: str) -> float:
    # Automatically traced
    events = await get_events(user_id)
    score = compute_score(events)
    return score
"""

import asyncio
