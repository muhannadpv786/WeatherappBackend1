# otel_setup.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import os

def setup_otel(app):
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({
                "service.name": "weather-backend-fastapi"
            })
        )
    )

    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True
    )

    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor().instrument()
