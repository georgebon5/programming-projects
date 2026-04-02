"""
Tests for OpenTelemetry distributed tracing utilities.
Verifies that tracing is fully opt-in and behaves as a no-op when disabled.
"""

import importlib
import os


# Ensure OTEL endpoint is not set so all tests run in the disabled state
os.environ.setdefault("OTEL_EXPORTER_ENDPOINT", "")


def _reload_tracing():
    """Return a fresh copy of the tracing module with _tracer reset to None."""
    import app.utils.tracing as tracing_mod
    # Reset global state between tests
    tracing_mod._tracer = None
    return tracing_mod


def test_setup_tracing_noop_when_endpoint_empty():
    """setup_tracing() must be a no-op (returns None, _tracer stays None)
    when OTEL_EXPORTER_ENDPOINT is empty (the default)."""
    tracing = _reload_tracing()

    result = tracing.setup_tracing(app=None, engine=None)

    assert result is None
    assert tracing._tracer is None


def test_get_tracer_returns_none_when_disabled():
    """get_tracer() must return None when tracing has not been initialised."""
    tracing = _reload_tracing()

    tracer = tracing.get_tracer()

    assert tracer is None


def test_trace_span_noop_when_disabled():
    """trace_span() must yield None and not raise when tracing is disabled."""
    tracing = _reload_tracing()

    entered = False
    span_value = "sentinel"

    with tracing.trace_span("test.operation", {"key": "value"}) as span:
        entered = True
        span_value = span

    assert entered, "Context manager body must be executed"
    assert span_value is None, "span must be None when tracing is disabled"


def test_trace_span_noop_no_attributes():
    """trace_span() must work without attributes argument when disabled."""
    tracing = _reload_tracing()

    with tracing.trace_span("test.operation") as span:
        assert span is None


def test_trace_span_is_reentrant_when_disabled():
    """Nested trace_span() calls must all be no-ops when disabled."""
    tracing = _reload_tracing()

    with tracing.trace_span("outer") as outer:
        with tracing.trace_span("inner") as inner:
            assert outer is None
            assert inner is None


def test_setup_tracing_does_not_raise_without_otel_packages(monkeypatch):
    """If OTEL packages are missing the app must not crash — graceful degradation."""
    import builtins
    import sys

    tracing = _reload_tracing()

    # Simulate OTEL packages being unavailable by patching the import
    original_import = builtins.__import__

    def _block_otel(name, *args, **kwargs):
        if name.startswith("opentelemetry"):
            raise ImportError(f"Simulated missing package: {name}")
        return original_import(name, *args, **kwargs)

    # Only trigger the import-guard path when endpoint is set
    monkeypatch.setattr(tracing.settings, "otel_exporter_endpoint", "http://localhost:4317")
    monkeypatch.setattr(builtins, "__import__", _block_otel)

    try:
        result = tracing.setup_tracing(app=None, engine=None)
    finally:
        monkeypatch.setattr(builtins, "__import__", original_import)

    # Must not raise — _tracer stays None because import failed
    assert tracing._tracer is None
