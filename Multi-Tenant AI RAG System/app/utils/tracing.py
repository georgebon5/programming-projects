"""
OpenTelemetry distributed tracing setup.
Disabled by default — set OTEL_EXPORTER_ENDPOINT to enable.
"""
import logging
from contextlib import contextmanager

from app.config import settings

logger = logging.getLogger(__name__)

_tracer = None


def setup_tracing(app=None, engine=None):
    """Initialize OpenTelemetry tracing if configured.

    Call during app startup. No-op if OTEL_EXPORTER_ENDPOINT is empty.
    """
    global _tracer

    if not settings.otel_exporter_endpoint:
        logger.info("OpenTelemetry tracing disabled (OTEL_EXPORTER_ENDPOINT not set)")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    except ImportError:
        logger.warning(
            "OpenTelemetry packages not installed — tracing unavailable. "
            "Install opentelemetry-sdk and opentelemetry-exporter-otlp to enable."
        )
        return

    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": "0.5.0",
        "deployment.environment": settings.environment,
    })

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    _tracer = trace.get_tracer("rag-system")

    # Instrument FastAPI
    if app:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
        except Exception:
            logger.debug("FastAPI instrumentation not available")

    # Instrument SQLAlchemy
    if engine:
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            SQLAlchemyInstrumentor().instrument(engine=engine)
        except Exception:
            logger.debug("SQLAlchemy instrumentation not available")

    # Instrument Redis
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor().instrument()
    except Exception:
        logger.debug("Redis instrumentation not available")

    # Instrument Celery
    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        CeleryInstrumentor().instrument()
    except Exception:
        logger.debug("Celery instrumentation not available")

    logger.info(
        "OpenTelemetry tracing enabled → %s (service=%s)",
        settings.otel_exporter_endpoint,
        settings.otel_service_name,
    )


def get_tracer():
    """Get the global tracer instance. Returns None if tracing is disabled."""
    return _tracer


@contextmanager
def trace_span(name: str, attributes: dict | None = None):
    """Create a trace span if tracing is enabled, otherwise no-op."""
    if _tracer is None:
        yield None
        return

    with _tracer.start_as_current_span(name, attributes=attributes or {}) as span:
        yield span
