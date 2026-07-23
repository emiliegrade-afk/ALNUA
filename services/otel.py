"""OpenTelemetry instrumentation — optional distributed tracing."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)
_instrumented = False


def setup_otel(*, service_name: str = "alnua-hub") -> None:
    """Initialize OTel tracing if OTEL_EXPORTER_OTLP_ENDPOINT is set."""
    global _instrumented
    if _instrumented:
        return
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        logger.info("OTel disabled — set OTEL_EXPORTER_OTLP_ENDPOINT to enable")
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        trace.set_tracer_provider(provider)
        HTTPXClientInstrumentor().instrument()
        _instrumented = True
        logger.info("OpenTelemetry enabled → %s", endpoint)
    except ImportError:
        logger.warning("opentelemetry packages missing — pip install opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-httpx")
    except Exception as exc:
        logger.warning("OTel setup failed: %s", exc)


def instrument_fastapi(app) -> None:
    """Mount FastAPI OTel middleware after app creation."""
    if not _instrumented:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
    except Exception as exc:
        logger.warning("FastAPI OTel instrumentation failed: %s", exc)
