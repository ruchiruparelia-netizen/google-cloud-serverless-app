"""Enterprise Structured JSON Logging & OpenTelemetry Observability Module for JPMC Agent Platform.

Configures `structlog` and `python-json-logger` to emit machine-parseable, Google Cloud Logging
compatible JSON payloads with automatic OpenTelemetry trace/span correlation and active PCI-DSS / PII
regex redaction across all agent, tool, memory, and API execution paths.
"""

import json
import logging
import re
import sys
from typing import Any, Dict, MutableMapping

import structlog

try:
    from pythonjsonlogger.json import JsonFormatter
except ImportError:  # pragma: no cover
    try:
        from pythonjsonlogger.jsonlogger import JsonFormatter  # type: ignore
    except ImportError:  # pragma: no cover
        JsonFormatter = None  # type: ignore

try:
    from opentelemetry import trace as otel_trace
except Exception:  # pragma: no cover
    otel_trace = None  # type: ignore


# Pre-compiled PCI-DSS & PII Redaction Patterns
_PAN_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
_SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CVV_KEY_NAMES = {"cvv", "cvc", "security_code", "pin", "otp"}


def redact_pci_pii_value(value: Any, key_name: str = "") -> Any:
    """Recursively scrubs raw 13-16 digit PANs, SSNs, and sensitive CVV/OTP fields for PCI-DSS compliance."""
    if key_name and key_name.lower() in _CVV_KEY_NAMES:
        return "***REDACTED_CVV***"
    if isinstance(value, str):
        scrubbed = _PAN_REGEX.sub("************REDACTED", value)
        scrubbed = _SSN_REGEX.sub("***-**-REDACTED", scrubbed)
        return scrubbed
    if isinstance(value, dict):
        return {k: redact_pci_pii_value(v, key_name=str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_pci_pii_value(item, key_name=key_name) for item in value]
    return value


def pci_pii_redaction_processor(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Structlog processor that enforces active regex-based PCI/PII redaction on every JSON log field."""
    for key, val in list(event_dict.items()):
        event_dict[key] = redact_pci_pii_value(val, key_name=str(key))
    return event_dict


def inject_opentelemetry_and_gcp_fields(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Structlog processor that injects Google Cloud Structured Logging severity and OTel trace context."""
    level = str(event_dict.get("level", method_name)).upper()
    event_dict["severity"] = level
    event_dict.setdefault("service", "jpmc-cross-channel-card-agent")
    event_dict.setdefault("component", "gemini-enterprise-agent-mesh")

    if otel_trace is not None:
        try:
            current_span = otel_trace.get_current_span()
            span_ctx = current_span.get_span_context() if current_span else None
            if span_ctx and getattr(span_ctx, "is_valid", False):
                trace_id_hex = format(span_ctx.trace_id, "032x")
                span_id_hex = format(span_ctx.span_id, "016x")
                event_dict.setdefault("trace_id", trace_id_hex)
                event_dict.setdefault("span_id", span_id_hex)
                event_dict["logging.googleapis.com/trace"] = f"projects/jpmc-agent-platform/traces/{trace_id_hex}"
                event_dict["logging.googleapis.com/spanId"] = span_id_hex
        except Exception:
            pass

    return event_dict


_LOGGING_CONFIGURED = False


def configure_structured_json_logging(level: int = logging.INFO) -> None:
    """Configures both `structlog` and standard library root handlers to emit structured JSON logs."""
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Replace any plain-text StreamHandlers with a JSON-formatted StreamHandler
    handler = logging.StreamHandler(sys.stdout)
    if JsonFormatter is not None:
        formatter = JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"levelname": "severity", "asctime": "timestamp"},
        )
        handler.setFormatter(formatter)
    root_logger.handlers = [handler]

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
            inject_opentelemetry_and_gcp_fields,
            pci_pii_redaction_processor,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(serializer=json.dumps),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=False,
    )
    _LOGGING_CONFIGURED = True


def get_structured_logger(name: str = "jpmc_agent", **initial_context: Any) -> Any:
    """Returns a configured `structlog` JSON logger bound with component metadata."""
    configure_structured_json_logging()
    return structlog.get_logger(name, logger_name=name, **initial_context)
